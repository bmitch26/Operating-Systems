# Shell and File System Project - Implementation of a basic shell
22 Oct 2024
5143 Shell Project
Group Members:
- Brett Mitchell, Sly Rahimi
- Note: P01 and P02 work together (shell interacts with the file system).

## Overview:
The goal of the project is to create a custom shell that interacts with a simulated filesystem managed through an SQLite database, allowing users to execute typical shell commands like ls, cp, mv, and grep. The shell leverages a FastAPI-based API to process user inputs, perform database operations, and handle file management tasks in a Linux-like environment.

## Instructions:
Download the files in P01 and P02, then run the `shell.py` file and use the following commands.

## Commands:
| Command  | Description                  | Author   |
|----------|------------------------------|----------|
| `ls`     | List files and directories    | Brett |
| `pwd`    | Print working directory       | Sly |
| `mkdir`  | Make new directory            | Sly |
| `cd, cd .., cd ~`     | Change directory | Brett |
| `mv`      | Move file/directory          | Brett/Sly |
| `cp`      | Copy file/directory          | Brett/Sly |
| `rm`      | Remove file/directory        | Brett |
| `cat`     | Display file(s)              | Brett |
| `less`    | Display file content one screen at a time | Sly |
| `head` | Shows the first few lines of a file | Sly |
| `tail` | Displays the last few lines of a file | Sly |
| `grep` | Searches for patterns within a file | Brett |
| `wc` | Provides word count for a file | Brett |
| `history` | Shows commands previously executed | Brett |
| `!x` | Shows a specific command in history | Sly |
| `chmod` | Change directory/file permissions | Sly/Brett |
| `sort` | Sort contents of a file            | Brett |
| `fortune` | Receive a fortune               | Sly |
| `cowspeak` | Display depiction of a coo    | Sly |
| `man` | Display additional command information | Sly |

## Non-Working Components
- 'pwd' has partial functionality; it returns the parent ID, but not the parent name.
- 'mv' worked in testing but gave issues in the live demo/presentation.
