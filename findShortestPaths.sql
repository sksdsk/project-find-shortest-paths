CREATE DATABASE SEP;
USE SEP;

CREATE TABLE Devices
(
    DeviceID INT PRIMARY KEY,
    DeviceName VARCHAR(255),
    IsSource BIT,
    IsDestination BIT,
    IsFaulted BIT,
    InUse BIT,
    Cost Int
);

CREATE TABLE Connections
(
    ConnectionID INT PRIMARY KEY,
    FromDeviceName VARCHAR(255),
    ToDeviceName VARCHAR(255),
    Cost INT
);



-- Add devices
INSERT INTO Devices
    (DeviceID, DeviceName, IsSource, IsDestination, IsFaulted, InUse)
VALUES
    (0, 'Source', 1, 0, 0, 0),
    (1, 'Diverter1', 0, 0, 0, 0),
    (2, 'Processor1', 0, 0, 0, 0),
    (3, 'Processor2', 0, 0, 0, 0),
    (4, 'Converter1', 0, 0, 0, 0),
    (5, 'Diverter1', 0, 0, 0, 0),
    (6, 'Destination1', 0, 1, 0, 0),
    (7, 'Destination2', 0, 1, 0, 0),
    (8, 'Destination3', 0, 1, 0, 0)

-- Add connections with a cost of 1
INSERT INTO Connections
    (ConnectionID, FromDeviceID, ToDeviceID, Cost)
VALUES
    (0, 0, 1, 1),
    -- Source to Converter1
    (1, 1, 2, 1),
    -- Source to Processor1
    (2, 1, 3, 1),
    -- Source to Processor2
    (3, 2, 4, 1),
    -- Processor1 to Converter1
    (4, 3, 4, 1),
    -- Processor2 to Converter1
    (5, 4, 5, 1),
    -- Converter1 to Diverter1
    (6, 5, 6, 1),
    -- Diverter1 to Destination1
    (7, 5, 7, 1),
    -- Diverter1 to Destination2
    (8, 5, 8, 1)  -- Diverter1 to Destination2
GO



--procedure to rm devices
CREATE PROCEDURE RemoveDevice
    @DeviceID INT
AS
BEGIN
    -- Remove connections related to the device
    DELETE FROM Connections WHERE FromDeviceID = @DeviceID OR ToDeviceID = @DeviceID;

    -- Remove the device
    DELETE FROM Devices WHERE DeviceID = @DeviceID;
END;
GO
EXEC RemoveDevice 8; 
GO

-- procedure to update the device info
CREATE PROCEDURE UpdateDevice
    @DeviceID INT,
    @DeviceName VARCHAR(255),
    @IsSource BIT,
    @IsDestination BIT,
    @IsFaulted BIT,
    @InUse BIT
AS
BEGIN
    -- Update the device
    UPDATE Devices 
    SET DeviceName = @DeviceName, 
        IsSource = @IsSource, 
        IsDestination = @IsDestination, 
        IsFaulted = @IsFaulted, 
        InUse = @InUse
    WHERE DeviceID = @DeviceID;
END;
GO
EXEC UpdateDevice 1, 'PROCESSOR0',1,0,0,1; 
GO

-- procedure to update the cost
CREATE PROCEDURE UpdateCost
    @ConnectionID INT,
    @Cost INT
AS
BEGIN
    -- Update the cost
    UPDATE Connections 
    SET Cost = @Cost
    WHERE ConnectionID = @ConnectionID;
END;
GO
EXEC UpdateCost 1, 2;
GO



CREATE PROCEDURE GetTop5ShortestPaths
    @SourceDeviceID INT,
    @DestinationDeviceID INT
AS
BEGIN
    -- Create a table to store the shortest paths
    CREATE TABLE #ShortestPaths
    (
        PathID INT IDENTITY(1,1),
        DeviceID INT,
        PrevDeviceID INT,
        Cost INT,
        PRIMARY KEY (PathID)
    );

    -- Initialize the table with the source device
    INSERT INTO #ShortestPaths
        (DeviceID, PrevDeviceID, Cost)
    VALUES
        (@SourceDeviceID, NULL, 0);

    -- Variable to store the current device ID
    DECLARE @CurrentDeviceID INT;

    -- Loop until the destination device is reached
    WHILE NOT EXISTS (SELECT 1
    FROM #ShortestPaths
    WHERE DeviceID = @DestinationDeviceID)
    BEGIN
        -- Get the device with the smallest cost that has not been visited yet and is not faulted or in use
        SELECT TOP 1
            @CurrentDeviceID = DeviceID
        FROM #ShortestPaths
        WHERE DeviceID NOT IN (SELECT FromDeviceID
            FROM Connections)
            AND DeviceID NOT IN (SELECT DeviceID
            FROM Devices
            WHERE IsFaulted = 1 OR InUse = 1)
        ORDER BY Cost;

        -- Insert all devices connected to the current device into the table, excluding faulted or in-use devices
        INSERT INTO #ShortestPaths
            (DeviceID, PrevDeviceID, Cost)
        SELECT ToDeviceID, @CurrentDeviceID, Cost + (SELECT Cost
            FROM #ShortestPaths
            WHERE DeviceID = @CurrentDeviceID)
        FROM Connections
        WHERE FromDeviceID = @CurrentDeviceID
            AND ToDeviceID NOT IN (SELECT DeviceID
            FROM #ShortestPaths)
            AND ToDeviceID NOT IN (SELECT DeviceID
            FROM Devices
            WHERE IsFaulted = 1 OR InUse = 1);
    END;

    -- Select the top 5 shortest paths
    SELECT TOP 5
        *
    FROM #ShortestPaths
    WHERE DeviceID = @DestinationDeviceID
    ORDER BY Cost;

    -- Drop the table
    DROP TABLE #ShortestPaths;
END;
GO

-- Test the function
EXEC GetTop5ShortestPaths 1, 8;
GO
