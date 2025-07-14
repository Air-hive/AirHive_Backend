**Back-end for AirHive 3D printing Management System**

**BACKEND**

**3.1	Introduction**

The **AirHive Local Backend** is a Flask-based web service that manages networked 3D printers for the AirHive printing management system. It automatically discovers AirHive printers on the local network (using mDNS/ZeroConf), maintains their status, and exposes a RESTful API for printer control (sending G-code commands, querying status, moving axes, uploading and starting prints) as well as managing a simple print job queue. Internally it uses **Flask** (a lightweight Python web framework) with **Flask-SQLAlchemy** (ORM) and **SQLite** to store print jobs. CORS support is enabled for cross-origin access, and the zeroconf library provides multicast DNS discovery of printers. All printer commands use standard 3D printer G-codes (e.g. M27 to report SD print status and M105 to request temperatures).

**3.2	System Use Case Diagram**

![A diagram of a computer

AI-generated content may be incorrect.](Aspose.Words.758a230d-a2f4-401c-9490-49a5ed7f0264.013.png)

Figure 3.1

The System Use Case Diagram illustrates the core functionalities of the AirHive Backend System and its interactions with primary actors. Key components include:

**Actors:**

1. User/Admin: Initiates control operations and manages the system
1. Frontend Client: Interfaces with the backend API
1. AirHive Printer: Physical device being managed

**Core Use Cases:**

- **Printer Discovery**: Automatic detection via mDNS/Zeroconf
- **Printer Control**: G-code execution, axis movement, homing
- **Status Monitoring**: Temperature, progress, and coordinate tracking
- **SD Card Management**: File uploads and print initiation
- **Job Queue Management**: CRUD operations for print jobs
- **System Administration**: Server configuration and monitoring

The diagram emphasizes the backend's role in coordinating printer communication, processing API requests, and maintaining system state through its Flask-based service architecture.

**3.3	API Reference**

The backend exposes a REST API under the /api prefix. All requests and responses use JSON. Below is a summary of the available endpoints. Sample request and response bodies are included where helpful.

- **GET /api/printers**

  Retrieves a list of discovered AirHive printers on the local network. Each printer object includes:

  - name: service name (e.g. "Airhive-XYZ").
  - hostname: mDNS hostname.
  - ip: printer’s IP address.
  - port: service port (usually 80).
  - status: "online" or "offline".
  - last\_seen: timestamp of last discovery (as string).
  - temperatures: initial temp placeholders.

**Example response:**

[

`  `{

`    `"name": "Airhive-ABC123",

`    `"hostname": "Airhive-ABC123.local",

`    `"ip": "192.168.1.42",

`    `"port": 80,

`    `"status": "online",

`    `"last\_seen": "1688641234.567",

`    `"temperatures": {

`      `"hotend": {"current": 0, "target": 0},

`      `"bed": {"current": 0, "target": 0}

`    `}

`  `},

`  `{ ... }

]

The service starts an mDNS discovery thread at launch. As printers announce themselves via Bonjour/mDNS[openprinting.github.io](https://openprinting.github.io/cups/doc/network.html#:~:text=Most%20network%20printers%20support%20a,TCP%2FIP%20and%20all%20of%20the), they are added to the list with status "online". Offline printers remain marked but will show "status": "offline" if not seen.

**3.3.1	Printers Commands & Status**

- **POST /api/send-command**

  Sends one or more raw G-code commands to a printer.

  **Request JSON:**

  {

  `  `"printer\_ip": "192.168.1.42",

  `  `"commands": ["G28", "G0 X10"]

  }

  This will POST the commands to http://<printer\_ip>/commands. No specific response body is defined (an empty 200 OK or error is returned). If missing parameters, it returns an error.

- **GET /api/update-responses/<printer\_ip>**

  Polls the printer for any pending responses. Internally it GETs http://<printer\_ip>/responses. The printer’s recent responses (e.g. acknowledgments, sensor readings) are appended to its internal buffer.

  **Response JSON:**

  {

  `  `"raw\_responses": ["ok", "T:200.0 /200.0", "SD printing byte 123/1000"]

  }

  The raw\_responses list contains lines of printer output accumulated since the last poll. (This endpoint is typically called internally by other API endpoints after sending a command to update the printer’s state.

- **GET /api/status/<printer\_ip>**

  Returns the print status of the printer (Idle, Printing, or Paused). This endpoint automatically sends M27 (report SD print status) to the printer and processes the response.

  **Response JSON:**

  {

  `  `"status": "Printing"

  }

  If no SD print is active, status will be "Idle". (G-code M27 reports progress like "SD printing byte 500/1000".)

- **GET /api/temperature/<printer\_ip>**

  Returns current temperatures. This sends M105 (report temperatures) and reads the response.

  **Response JSON:**

  {

  `  `"hotend\_temperature": 200.5,

  `  `"heatbed\_temperature": 60.0

  }

  These values reflect the printer’s current hotend and bed temperatures. (G-code M105 requests a temperature report[marlinfw.org](https://marlinfw.org/docs/gcode/M105.html#:~:text=Description).)

- **GET /api/print-progress/<printer\_ip>**

  Returns print progress percentage. Sends M27 and computes progress from the X/Y bytes reported.

  **Response JSON:**

  {

  `  `"Progress": 34.5

  }

  This is the percentage of the SD print completed.

- **GET /api/elapsed-time/<printer\_ip>**

  Returns elapsed print time. Sends M31 (report print time) and returns the printer’s elapsed\_time string.

  **Response JSON:**

  {

  `  `"elapsed\_time": "00:05:12"

  }

**3.3.2	Printer Motion & Axes**

- **POST /api/home/<printer\_ip>**

  Homes the printer axes.

  **Request JSON:**

  {

  `  `"axis-to-home": ["X", "Y"]  // or ["all"] to home all axes

  }

  Sends G28 X, G28 Y, etc. to home specified axes (if "all" is given, it homes all axes). Returns the new coordinates after homing.

  **Response JSON:**

  {

  `  `"x\_coordinate": 0.0,

  `  `"y\_coordinate": 0.0,

  `  `"z\_coordinate": 0.0

  }

  If an invalid axis is given, returns a 400 error {"error": "Wrong json fields"}.

- **POST /api/move\_axis/<printer\_ip>**

  Moves the printer head by specified distances (relative move).

  **Request JSON:**

  {

  `  `"x\_distance": 10,

  `  `"y\_distance": -5,

  `  `"z\_distance": 0.3,

  `  `"e\_distance": 2

  }

  Each field is optional meaning that it is not necessary that all fields exist, only those that exist in the request body will be moved. It sends a G0 command with the given distances (in relative mode, preceded by G91).

  **Response JSON:**

  {

  `  `"x\_coordinate": 10.0,

  `  `"y\_coordinate": -5.0,

  `  `"z\_coordinate": 0.3,

  `  `"e\_coordinate": 2.0

  }

  The coordinates reflect the new position after the move.

- **GET /api/axis-coordinates/<printer\_ip>**

  Queries the current axis coordinates by sending M114.

  **Response JSON:**

  {

  `  `"X": 10.0,

  `  `"Y": -5.0,

  `  `"Z": 0.3

  }

**3.3.3	SD Card File Operations**

- **POST /api/upload-to-sdcard/<printer\_ip>**

  Uploads a G-code file to the printer’s SD card via HTTP.

  **Request JSON:**

  {

  `  `"file\_name": "example.gcode",

  `  `"file\_path": "/path/to/example.gcode"

  }

  The backend reads the specified local file (using absolute file\_path on the server), streams it to the printer in chunks using M28/M29 G-codes, and then lists the SD card contents.

  **Response JSON:**

  {

  `  `"sdcard-files": ["example.gco", "test.gco", ...]

  }

  The response is the updated list of files on the printer’s SD card (parsed by the PrinterInfo class). Note that the code truncates the filename to 8 characters + .gco.

- **POST /api/print-file/<printer\_ip>**

  Starts printing a file from the printer’s SD card.

  **Request JSON:**

  {

  `  `"filename": "example.gco"

  }

  The backend sends M21 (mount SD), M23 <filename> (select file), and M24 (start print).

  **Response JSON:**

  {

  `  `"Printing": "example.gco"

  }

  The printer will begin printing the specified file.

**3.3.4	Print Job Queue (Database)**

This set of endpoints manages a simple print job queue stored in SQLite via SQLAlchemy.

- **POST /api/jobs** – Create a new job.

  **Request JSON:**

  {

  `  `"file\_name": "part.gcode",

  `  `"file\_path": "/files/part.gcode",

  `  `"priority": 1

  }

  **Response JSON:**

  {

  `  `"id": 1,

  `  `"file\_name": "part.gcode",

  `  `"file\_path": "/files/part.gcode",

  `  `"priority": 1

  }

  Returns the created job with its new id. All fields are required, or a 400 error is returned.

- **GET /api/jobs** – List all jobs.

  **Response JSON:**

  [

  `  `{"id": 1, "file\_name": "part.gcode", "file\_path": "/files/part.gcode", "priority": 1},

  `  `{"id": 2, ...}

  ]

- **GET /api/jobs/<job\_id>** – Retrieve a specific job by ID.

  **Response JSON:**

  {

  `  `"id": 1,

  `  `"file\_name": "part.gcode",

  `  `"file\_path": "/files/part.gcode",

  `  `"priority": 1

  }

  Returns 404 if not found.

- **PUT /api/jobs/<job\_id>** – Update a job.

  **Request JSON:** (fields to update)

  {

  `  `"file\_name": "updated.gcode",

  `  `"priority": 2

  }

  **Response JSON:** (the updated job)

  {

  `  `"id": 1,

  `  `"file\_name": "updated.gcode",

  `  `"file\_path": "/files/part.gcode",

  `  `"priority": 2

  }

- **DELETE /api/jobs/<job\_id>** – Delete a job.

  **Response JSON:**

  { "message": "Job deleted" }



**3.4	Database Schema**

The only database table is **job\_model**, defined by the JobModel class (using Flask-SQLAlchemy). Its fields are:

|**Column**|**Type**|**Description**|
| :-: | :-: | :-: |
|id|Integer (PK)|Primary key (auto-increment)|
|file\_name|String(100)|Name of the G-code file (required)|
|file\_path|String(255)|Path to the file (required)|
|priority|Integer|Job priority (required)|

This ORM model maps to the SQLite table for storing print jobs. An example CREATE TABLE (conceptual) is:

CREATE TABLE job\_model (

`    `id INTEGER PRIMARY KEY,

`    `file\_name VARCHAR(100) NOT NULL,

`    `file\_path VARCHAR(255) NOT NULL,

`    `priority INTEGER NOT NULL

);

**3.5	Backend Structure**

The backend files are organized as follows:

- **app.py**: Main Flask application and API route definitions. Initializes the app, database (SQLAlchemy), CORS, and starts mDNS discovery. Defines routes for printer control and job queue.
- **mdns.py**: Multicast DNS (zeroconf) discovery module. Continuously browses for services of type \_http.\_tcp.local. with names starting “Airhive”. Discovered printers are stored in discovered\_printers (with metadata) and printers (a mapping IP→Printer object for state). Runs in a background thread.
- **PrinterInfo.py**: Contains the Printer class that holds state for each printer (coordinates, temperatures, status, SD files, etc.). Its update\_printer\_variables method parses raw printer responses (lines from M105, M114, SD status, etc.) to update these fields.
- **PrinterToBackend.py**: Helper functions that send HTTP requests *to* the printers. Functions include:
  - send\_commandd\_to\_printer(ip, commands): POSTs G-code commands to a printer’s /commands endpoint.
  - get\_responses\_from\_printer(ip, size): GETs printer’s /responses endpoint for the next size bytes.
  - config\_printer(ip, baudrate): PUTs to /machine-config to set baud rate (printer configuration).

    These functions wrap the requests library and return JSON/errors.

- **queue\_endpoints.py**: API routes for managing the print job queue (CRUD operations). It uses the JobModel ORM (imported from models, although the class is actually defined in app.py) and handles JSON input/output for jobs.
- **UploadFileToPrinter.py**: Implements file upload to a printer’s SD card. Breaks a local G-code file into chunks (45KB each), prefixes each line with line numbers and checksums, and sends them to the printer via G-codes M28 (start write) and M29 (stop write) using the helper. After uploading, the printer’s SD directory list is updated.

![A diagram of a computer program

AI-generated content may be incorrect.](Aspose.Words.758a230d-a2f4-401c-9490-49a5ed7f0264.014.png)

Figure 3.2

- **models.py**: (Empty or placeholder file; note: the JobModel is defined in app.py.)
- **.git/** and **\_\_pycache\_\_/**: Git and Python cache files (not part of runtime).
- **uploads/**: Directory for storing files to be uploaded to printers (as configured by the app).

**3.6	Usage Guide**

- **Testing the API:** Use tools like Postman or curl to exercise the API.
- **Order of Operations:** Typically, first call /api/printers to find available printers. Then use the printer’s IP from that list for subsequent calls. 
- **Postman Collection:** (Optional) You can import a Postman collection or define environments for printer\_ip to streamline testing.
- **Error Handling:** If an endpoint receives invalid JSON or missing fields, it returns an error with an appropriate HTTP status (e.g. 400). Check response codes and JSON error messages.
- **Concurrent Use:** Multiple clients can use the API simultaneously. The backend uses a thread lock (printer\_lock) to synchronize access to shared printer state when discovering printers or updating lists.








**3.7	Development Notes**

**3.7.1	mDNS Discovery**

The mdns.go() function starts a daemon thread that continuously browses for \_http.\_tcp.local. services. When a printer named “Airhive...” announces itself (Bonjour/ZeroConf), the PrinterServiceListener adds it to discovered\_printers.

![A diagram of a network

AI-generated content may be incorrect.](Aspose.Words.758a230d-a2f4-401c-9490-49a5ed7f0264.015.png)

Figure 3.3

This allows plug-and-play detection of printers without manual IP configuration [openprinting.github.io](https://openprinting.github.io/cups/doc/network.html#:~:text=Most%20network%20printers%20support%20a,TCP%2FIP%20and%20all%20of%20the).

2. **Printer State**

Each printer’s state is tracked by a Printer object (in PrinterInfo.py). Commands and sensor data received from the printer (via HTTP responses) are parsed and stored (temperatures, coordinates, progress, SD file list). This simulates a real printer’s variables on the backend side. The following diagram visualize the sequence of actions involved in updating the printer state.

![A screenshot of a computer

AI-generated content may be incorrect.](Aspose.Words.758a230d-a2f4-401c-9490-49a5ed7f0264.016.png)

Figure 3.4










**3.7.3	Command Execution Sequence**

Illustrates the end-to-end flow when the backend processes printer commands (e.g., via /api/send-command). This diagram clarifies interactions between API endpoints, printer communication, and state updates.

![A diagram of a computer program

AI-generated content may be incorrect.](Aspose.Words.758a230d-a2f4-401c-9490-49a5ed7f0264.017.png)

Figure 3.5

**3.7.4	Threading**

mDNS runs in its own thread so as not to block Flask. API calls that send commands (like /home or /move\_axis) rely on updating state by calling update\_responses after sending a command. Be cautious: calls like /api/send-command do not wait for a response, whereas status endpoints do M27 or M105 calls and then update the state.

**3.7.5	Simulated Environment**

` `(If no physical AirHive printer is available, one could simulate by running a dummy HTTP server at a test IP that accepts the /commands and /responses endpoints with expected behavior. The current code assumes real printers implement a REST interface for G-codes.)

**3.7.6	Database Sync**

` `On app start, db.create\_all() is called before serving requests to ensure the job\_model table exists.

