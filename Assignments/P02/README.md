# Shell Project - Implementation of a Unix/Linux Shell
https://www.youtube.com/watch?v=mKiKkYp8C88

22 Oct 2024
- 5143 Shell Project
Group Members:
- Brett Mitchell, Sly Rahimi
- Note: P01 and P02 work together (shell interacts with the file system).

## Overview:
- The goal of the project is to create a Unix/Linux style shell with implementation of various common commands. This includes the execution typical shell commands like ls, cp, mv, and grep. The shell leverages a FastAPI-based API to process user inputs, perform database operations, and handle file management tasks.

## Files:
| File  | Description                  |
|----------|------------------------------|
| shell.py | Contains all of the initial logic for sending requests to api.py in P01 for handling commands. |
| getch.py | Contains logic relevant to command logic keyboard movement. |
| fortunes.txt | A txt file with 100 different 'fortunes', or sentences of text that can be fetched with the 'fortune' command. |

## Instructions:
Download all of the files in P01 and run any of the following commands after populating the database with 'create_and_load_db.py':

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
