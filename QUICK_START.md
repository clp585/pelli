# Quick Start Guide - AI Node Editor

## Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (use your existing venv if preferred)
pip install -r requirements.txt

# Start the server
python run_server.py
```

The backend will run on `http://localhost:5000`

### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. **Open the app** in your browser: `http://localhost:3000`

2. **Add a node**: 
   - Click on an agent in the left sidebar (e.g., "Nano Variant Render")
   - The node will appear on the canvas

3. **Configure a node**:
   - Click on a node to select it
   - Configure parameters in the sidebar (e.g., lighting_mode, style_name)

4. **Connect nodes**:
   - Drag from an output port (right side) to an input port (left side)
   - This connects the output of one node to the input of another

5. **Execute the graph**:
   - Click "Execute Graph" in the top toolbar
   - Nodes will execute in the correct order (respecting dependencies)
   - Results will appear on each node

## Example Workflow

1. Add a "Nano Variant Render" node
2. Configure it:
   - `image_path`: path to your input image (e.g., "image.jpg")
   - `lighting_mode`: "night"
   - `style_name`: "modern"
3. Click "Execute Graph"
4. The node will process and show the output path in the result

## Troubleshooting

- **Backend not starting**: Make sure you're in the backend directory and have installed requirements
- **Frontend can't connect**: Ensure backend is running on port 5000
- **Agents not showing**: Check backend logs for import errors
- **Execution fails**: Check node configuration - required inputs must be provided

