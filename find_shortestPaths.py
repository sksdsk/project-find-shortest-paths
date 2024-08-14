import pandas as pd
import pyodbc
import networkx as nx
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# Load the Excel file
df = pd.read_excel("Device list.xlsx")
# print(df)

# Establish a connection to the SQL Server
# conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-SKSDSK\SQLEXPRESS;DATABASE=PATHS;Trusted_Connection=yes')
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-SKSDSK\SQLEXPRESS;DATABASE=PATHS;Trusted_Connection=yes')
cursor = conn.cursor()


def create_device_table():
    # Delete extra rows from Devices table
    cursor.execute("DELETE FROM Devices")
    conn.commit()
    # Reset the identity seed so that DeviceID starts from 1 again
    cursor.execute("DBCC CHECKIDENT ('Devices', RESEED, 0)")
    conn.commit()

    # Insert data into Devices table
    for index, row in df.iterrows():
        # Check if the device is faulted
        is_faulted = row.get('IsFaulted', 0)
        if is_faulted:
            continue  # Skip this device if it's faulted

        cost = 1 if not (row['Is Source'] or row['Is Destination']) else 0
        cursor.execute(
            """
            INSERT INTO Devices (DeviceName, IsSource, IsDestination, IsFaulted, InUse, Cost)
            VALUES (?, ?, ?, ?, ?, ?)
            """, 
            row['Plant Item'], row['Is Source'], row['Is Destination'], is_faulted, 1, cost)
    conn.commit()

def create_connections():
    # Delete extra rows from Devices table
    cursor.execute("DELETE FROM Connections")
    conn.commit()
    # Reset the identity seed so that DeviceID starts from 1 again
    cursor.execute("DBCC CHECKIDENT ('Connections', RESEED, 0)")
    conn.commit()

    # Insert data into Connections table
    for index, row in df.iterrows():
        if pd.notna(row["Connect from"]):
            # Check if connection already exists
            cursor.execute(
                """
                SELECT COUNT(*) FROM Connections
                WHERE FromDeviceName = ? AND ToDeviceName = ?
                """,
                row["Connect from"],
                row["Plant Item"],
            )
            
            if cursor.fetchone()[0] == 0:
                # Insert connection from 'Connect from' to 'Plant Item'
                cursor.execute(
                    """
                    INSERT INTO Connections (FromDeviceName, ToDeviceName, Cost)
                    VALUES (?, ?, ?)
                """,
                    row["Connect from"],
                    row["Plant Item"],
                    1,
                )

        if pd.notna(row["Connect to"]):
            # Check if connection already exists
            cursor.execute(
                """
                SELECT COUNT(*) FROM Connections
                WHERE FromDeviceName = ? AND ToDeviceName = ?
                """,
                row["Plant Item"],
                row["Connect to"],
            )
            if cursor.fetchone()[0] == 0:
                # Insert connection from 'Plant Item' to 'Connect to'
                cursor.execute(
                    """
                    INSERT INTO Connections (FromDeviceName, ToDeviceName, Cost)
                    VALUES (?, ?, ?)
                    """,
                    row["Plant Item"],
                    row["Connect to"],
                    1,
                )

    conn.commit()

    # # pritn data from Connections table
    # cursor.execute("SELECT * FROM Connections")
    # connections = cursor.fetchall()
    # print("\nConnections:")
    # for connection in connections:
    #     print(connection)
    # return


def find_shortest_paths(source, targets):
    # Fetch data from Connections table
    cursor.execute("SELECT * FROM Connections")
    data = cursor.fetchall()

    # Fetch data from Devices table
    cursor.execute("SELECT * FROM Devices")
    devices = cursor.fetchall()
    device_costs = {device.DeviceName: device.Cost for device in devices}


    # Create a graph
    G = nx.DiGraph()

    # Add edges to the graph
    for row in data:
        cost = (row.Cost or 0) + (device_costs.get(row.FromDeviceName, 0) or 0)/2 + (device_costs.get(row.ToDeviceName, 0) or 0)/2
        G.add_edge(row.FromDeviceName, row.ToDeviceName, weight=cost, edgeCost=row.Cost)

    # Find the multiple shortest paths from source to target
    # 循环每一个 target
    pathes = []
    
    for target in targets:
        pathes.append(nx.shortest_simple_paths(G, source, target, weight="weight"))

    
    # 返回的数据结构 :  [group:5][destination:n][cost, path] : 5:终点数量:1+Path数量
    pathes =  get_top_pathes(pathes, G)
    
    # 确定每个 group 有几个 node 是相同的
    groupSameNodeAmount = get_same_node_amount(pathes)

    # print("Group same node amount: ", groupSameNodeAmount)

    # 计算 overall cost：减去从 第一个 到 相同的node 的 cost
    groupOverallCost = []
    for groupIndex, group in enumerate(pathes):
        sameNodeAmount = groupSameNodeAmount[groupIndex]
        overallCost = 0
        for targetIndex, path in enumerate(group):
            # sameCost = 0

            # 减去 Edge
            overallCost += path[0] - sum(G.edges[path[n], path[n + 1]]["edgeCost"] for n in range(1, sameNodeAmount))
            # sameCost += sum(G.edges[path[n], path[n + 1]]["edgeCost"] for n in range(1, sameNodeAmount))

            # print("Same edge cost: ", sameCost)
            
            # 减去每个 node 的 cost
            for nodeIndex in range(1, sameNodeAmount+1):
                overallCost -= device_costs.get(path[nodeIndex], 0)
                # sameCost += device_costs.get(path[nodeIndex], 0)

            # print("Same cost: ", sameCost)

        groupOverallCost.append(overallCost)
            
    # print("Group overall cost: ", groupOverallCost)
    
    # 显示最终结果
    for groupIndex, group in enumerate(pathes):
        print("Group: ", groupIndex)
        print("Overall cost: ", groupOverallCost[groupIndex])

        
        for targetIndex, path in enumerate(group):
            print("\nTarget: ", targets[targetIndex])
            
            for nodeIndex, node in enumerate(path):
                if nodeIndex == 0:
                    print("Cost: ", node)
                elif nodeIndex == len(path) - 1:
                    print(node)
                else:
                    print(node, end=" -> ")
            
        print("\n--------------------------------------------------")


    cursor.close()
    conn.close()

# 获取前五个 path
# 返回的数据结构 :  [group:5][destination][cost, path] : 5:终点数量:1+Path数量
def get_top_pathes(pathes, G):
    # Get as many paths as possible, up to five, 获取每一个 target 的前五个 path
    top_pathes = []
    
    for index, _ in enumerate(pathes):
        five_path = []
        
        paths = pathes[index]
        for _ in range(5):
            try:
                path = next(paths)
                pathCopy = path.copy() 

                path_cost = sum(
                    G.edges[path[n], path[n + 1]]["weight"] for n in range(len(path) - 1)
                )
                pathCopy.insert(0, path_cost)
                five_path.append(pathCopy)
            
            except StopIteration:
                break

        top_pathes.append(five_path)

    
    final = []
    # 更换数据结构
    for i in range(5):
        group = []
        for index, _ in enumerate(pathes):
            group.append(top_pathes[index][i])

        final.append(group)

    
    
    return final


# 确定每个 group 有几个 node 是相同的
def get_same_node_amount(pathes):
    # 确定每个 group 有几个 node 是相同的
    groupSameNodeAmount = []

    for groupIndex, group in enumerate(pathes):

        # 确定 到第几位 path 是相同的 第 0 位是 cost
        sameNode = 1
        
        # 确定到第几位 path 是相同的
        while True:
            
            # 初始化
            node = group[0][sameNode]
            finished = False
            
            for targetIndex, path in enumerate(group):
                if node != path[sameNode]:
                    finished = True
                    break

            
            
            if finished:
                break
            else:
                sameNode += 1

        # 去除 Cost 导致的 +1 和 最后一次循环的 +1
        groupSameNodeAmount.append(sameNode - 1)

    return groupSameNodeAmount




def update_connection_cost(from_device, to_device, cost):
    # Prepare the SQL query
    sql = """
    UPDATE Connections
    SET Cost = ?
    WHERE FromDeviceName = ? AND ToDeviceName = ?
    """

    # Execute the SQL query
    cursor.execute(sql, cost, from_device, to_device)

    # Commit the changes
    conn.commit()

def update_device_cost(device_name, cost):
    # Prepare the SQL query
    sql = """
    UPDATE Devices
    SET Cost = ?
    WHERE DeviceName = ?
    """

    # Execute the SQL query
    cursor.execute(sql, cost, device_name)

    # Commit the changes
    conn.commit()

def make_device_faulted(device_name):
    # Prepare the SQL query
    sql = """
    UPDATE Devices
    SET IsFaulted = ?
    WHERE DeviceName = ?
    """

    # Execute the SQL query
    cursor.execute(sql, 1, device_name)

    # Commit the changes
    conn.commit()

def mark_connection_faulted(from_device, to_device):
    # Mark the connection as faulted in the Connections table
    sql = """
    UPDATE Connections
    SET IsFaulted = 1
    WHERE FromDeviceName = ? AND ToDeviceName = ?
    """
    cursor.execute(sql, from_device, to_device)
    conn.commit()


create_device_table()
create_connections()

make_device_faulted('CLEAN104')
mark_connection_faulted('CLEAN104', 'DIVERTER3')
# update_connection_cost('CLEAN104', 'DIVERTER3', 2)
update_device_cost('SOURCE_8', 3)
find_shortest_paths("SOURCE_8", ["DEST11", "DEST6"])
