# ACM Hackathon 2025 Devcontainer Setup


## Prerequisites

- **Visual Studio Code**
  [Download and install VS Code](https://code.visualstudio.com/).

- **DevContainers Extension**
  Install the "DevContainers" extension:
  - Open VS Code.
  - Navigate to the extension store or Press `Ctrl+P` (or `Cmd+P` on macOS) and type:
    ```
    ext install devcontainers.devcontainers
    ```


## Setup Instructions

1. **Clone the Repository**
   Open your terminal and run:
   ```bash
   git clone git@github.com:IsaiahHarvi/acm-hackathon-2025.git
   cd acm-hackathon-2025
   ```

2. **Open the ACM Hackathon Directory in VS Code**
   - Open VS Code.
   - Navigate to **File** > **Open Folder…**.
   - Select the `acm-hackathon-2025` directory.

3. **Reopen the Folder in a Dev Container**
   - Press `F1` (or `Ctrl+Shift+P` / `Cmd+Shift+P` on macOS) to open the Command Palette.
   - Type:
     ```
     Reopen in Container
     ```
   - Select the `DevContainers: Reopen in Container` command.

4. **Select CPU or GPU Devcontainer**
   - When the container starts, you'll be prompted to choose between CPU and GPU configurations.
     - Choose your desired configuration:
       - **CPU**: Standard development container.
       - **GPU**: For systems with Nvidia GPUs

5. **Git Config**
    - Run:
    ```
    git config --global user.email "YourGithubEmail"
    git config --global user.name "YourGithubUsername"
    ```

## Troubleshooting

- **Extension Issues:**
  Ensure that both VS Code and the **DevContainers** extension are up to date.

- **Container Reopening:**
  If the container does not start as expected, try restarting VS Code and repeating the "Reopen in Container" steps.

---

## Additional Resources

- [VS Code DevContainers Documentation](https://code.visualstudio.com/docs/devcontainers/overview)
- [GitHub DevContainers Repository](https://github.com/devcontainers)
