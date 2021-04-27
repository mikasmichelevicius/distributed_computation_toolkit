# Distributed Computation Toolkit

A prototype system of distributed computation tool. The system accepts multiple jobs for execution that are distributed among the cluster of connected Worker Nodes.


## Command-line Interface Usage
To get started with the program, each component - Server, Control Client and Worker Client have to be run in separate terminal windows.
### 1. Run the Server
Open a new terminal window for the root directory of the repository and enter:
```bash
cd server/
python run_servers.py
```

### 2. Run the Worker Client
Open a new terminal window for the root directory of the repository and enter:
```bash
cd client/
python client.py localhost 5002
```
Multiple Worker Clients can be run for testing purposes in different terminal windows.

### 3. Run the Control Client
Open a new terminal window for the root directory of the repository and enter:
```bash
cd website/
python control_client.py localhost 5002
```

Now the *control_client.py* program will display a control panel. First, enable the command-line interface usage by typing the ***enable*** command. Then select one of the features by entering one of the specified commands.

### 4. Submit a Job
To submit a job for execution via the command-line interface, the submission file together with executable and dataset must be in the same directory as *control_client.py* program. Several test programs together with an executable and dataset, if applicable, are prepared in the *TESTS/* directory. Since the *control_client.py* file is located in the website directory, before running the Control Client program, first copy a test job and its files to the *website/* directory. For example, let's submit a job1 for execution, first copy all the files from the *TESTS/job1/* directory to the *website/* directory:
```bash
cp TESTS/job1/* website/
```

Then, run the Control Client program (If the Server and at least one Worker Node is already running):
```bash
cd website/
python control_client.py localhost 5002
```

Then, enable the command-line interface usage by typing ***enable*** command and enter the:
***SUBMIT submission_file1.txt*** (Since the copied documents from *job1* directory contains a submission file called *submission_file1.txt*, *submission_file2.txt* for *job2*, etc). Once the Worker Node finishes executing the submitted job, the Control Client program output will display notification that the job was completed and will display the name of the directory where the results of the task will be stored.


## Web Interface Usage

### 1. Run the Server
Run the server in the same way as described for the command-line interface usage.

### 2. Run the Worker Node
Run the worker node in the same way as described for the command-line interface usage.

### 3. Run the Control Client and Website
Open a new terminal window for the root directory of the repository and enter:
```bash
cd website/
python run_user.py
```
The command below will run the control client application as well as Django web server.
Open the browser and enter the URL address - *localhost:7000/computation/home/*. Use the application, submit a job in the Job Submission page. 
