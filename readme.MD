# Installation Guide for hubbard_ai

Follow these instructions to install and run the `hubbard_ai` project.

## Step 1: Clone the GitHub Repository

First, clone the repository by running the following command in your terminal:

```
git clone https://github.com/abdulzain6/hubbard_ai
```

## Step 2: Navigate to the Directory

Move into the `hubbard_ai` directory:

```
cd hubbard_ai
```

## Step 3: Build the Docker Image

Build the Docker image using the following command:

```
sudo docker build . -t hubbard_ai
```

This will build a Docker image with the tag `hubbard_ai`.

## Step 4: Run the Docker Container

Finally, run the Docker container with the following command:

```
sudo docker run --net=host hubbard_ai
```

This will start the `hubbard_ai` container, and you should now have access to the application.

## Troubleshooting

If you encounter any issues during the installation process, please check the project's documentation or contact the maintainers for assistance.

---

Happy coding!
