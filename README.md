# Firefly III Synchronization Tool

This project provides a comprehensive Python-based solution for managing and synchronizing financial data between Kresus - a personal finance management tool, and Firefly III - an open-source personal finance manager. It's designed to streamline the process of financial data handling, offering seamless integration and data synchronization capabilities.

A python documentaion is available [here](https://alanjumeaucourt.github.io/firefly-iii-synchro/)

## Features
Firefly III API Integration: Utilizes a custom-built wrapper around the Firefly III API, enabling efficient interactions such as fetching, creating, updating, and deleting financial records.

- Kresus Data Processing: Handles data obtained from Kresus, effectively parsing and preparing it for synchronization with Firefly III.
Kresus offer automatically synchro with a lots of bank accounts

- Data Synchronization: Offers functionalities to sync accounts and transactions from Kresus to Firefly III, ensuring data consistency across platforms.

- Local Data Management: Supports reading and processing local financial data, providing a bridge between local data sources (excel) and Firefly III.

- CSV Export: Includes utility functions for exporting financial data to CSV files, aiding in data backup and reporting.

- Logging and Configuration: Features a robust logging system for monitoring and debugging, along with .env based configuration management for enhanced security and customization.

## Usage

The tool's main module orchestrates various components, including API interactions, data processing, and synchronization tasks. It's designed for ease of use and can be adapted to different user requirements.

## Getting Started

1. Clone the repository.
1. Set up your .env file with necessary API keys and endpoints.
1. build and lauch the container `docker build --pull --rm -f "Dockerfile" -t fireflyiiisynchro:latest "." && docker run -it fireflyiiisynchro`
`
