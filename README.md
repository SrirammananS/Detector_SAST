# Detector_SAST

Welcome to the Source Code Review Detector Tool! This tool is designed to assist with source code review processes by identifying vulnerable words or phrases within source code files. Developed using Python, this tool offers an independent solution for conducting source code analysis on Windows platforms.

## Features:
* Independently Executable: The tool is designed to run independently on Windows operating systems, ensuring flexibility and ease of use.

* Input Parameters: It takes input in the form of source code files and a list of vulnerable words or phrases to search for.

* Search and Highlight: The tool scans the provided source code folder for occurrences of the specified vulnerable words or phrases. When found, it highlights the iterations, line numbers, and previews the affected code within the Notepad++ text editor.

* Automated Navigation: Upon detection of a vulnerable instance, the tool automatically navigates to the respective line within the Notepad++ window, providing quick access for further review and action.

## Requirements:
* Operating System: Windows
* Software: Notepad++ (for code preview)
* Python Environment: Ensure Python is installed and accessible in your system environment variables.
