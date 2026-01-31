from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import json

router = APIRouter(prefix="/settings", tags=["settings"])

# Đường dẫn tới thư mục settings
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'settings')
os.makedirs(SETTINGS_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')

# Đường dẫn tới thư mục workflows
WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'workflow', 'saved_workflows')

# Mô hình cho default workflow
class DefaultWorkflow(BaseModel):
    workflow_id: Optional[str] = None
    data_workflow_id: Optional[str] = None

@router.get("/get")
async def get_settings():
    """Get current settings"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            # Default settings if file doesn't exist
            settings = {
                "workflow_settings": {
                    "default_workflow_id": None,
                    "default_data_workflow_id": None
                }
            }
            # Save default settings
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "settings": settings}
    except Exception as e:
        return {"success": False, "message": f"Error getting settings: {str(e)}"}

@router.post("/save")
async def save_settings(settings: Dict[str, Any] = Body(...)):
    """Save settings"""
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": "Settings saved successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error saving settings: {str(e)}"}

@router.post("/set_default_workflows")
async def set_default_workflows(data: dict):
    """Set default workflows"""
    try:
        print(f"Setting default workflows: {data}")  # Debug log
        
        # Load existing settings
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Ensure workflow_settings exists
        if "workflow_settings" not in settings:
            settings["workflow_settings"] = {}
        
        # Update workflow settings
        workflow_settings = settings["workflow_settings"]
        
        if "workflow_id" in data:
            workflow_settings["default_workflow_id"] = data["workflow_id"]
            print(f"Set default_workflow_id: {data['workflow_id']}")
        
        if "data_workflow_id" in data:
            workflow_settings["default_data_workflow_id"] = data["data_workflow_id"]
            print(f"Set default_data_workflow_id: {data['data_workflow_id']}")
        
        # Save settings
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print(f"Settings saved to: {SETTINGS_FILE}")
        return {"success": True, "message": "Default workflows updated successfully"}
        
    except Exception as e:
        print(f"Error setting default workflows: {str(e)}")
        return {"success": False, "message": f"Error setting default workflows: {str(e)}"}

@router.get("/get_default_workflows")
async def get_default_workflows():
    """Get default workflows with their data"""
    try:
        print(f"Getting default workflows from: {SETTINGS_FILE}")
        
        # Get settings
        if not os.path.exists(SETTINGS_FILE):
            print("Settings file not found")
            return {
                "success": True,
                "default_workflow": None,
                "default_data_workflow": None,
                "message": "No settings found"
            }
        
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        workflow_settings = settings.get("workflow_settings", {})
        default_workflow_id = workflow_settings.get("default_workflow_id")
        default_data_workflow_id = workflow_settings.get("default_data_workflow_id")
        
        print(f"Found workflow IDs - workflow: {default_workflow_id}, data: {default_data_workflow_id}")
        
        result = {
            "success": True,
            "default_workflow": None,
            "default_data_workflow": None
        }
        
        # Load default workflow if exists
        if default_workflow_id:
            workflow_file = os.path.join(WORKFLOWS_DIR, f"{default_workflow_id}.json")
            print(f"Looking for workflow file: {workflow_file}")
            if os.path.exists(workflow_file):
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    result["default_workflow"] = json.load(f)
                print("Default workflow loaded successfully")
            else:
                print("Default workflow file not found")
        
        # Load default data workflow if exists
        if default_data_workflow_id:
            data_workflow_file = os.path.join(WORKFLOWS_DIR, f"{default_data_workflow_id}.json")
            print(f"Looking for data workflow file: {data_workflow_file}")
            if os.path.exists(data_workflow_file):
                with open(data_workflow_file, 'r', encoding='utf-8') as f:
                    result["default_data_workflow"] = json.load(f)
                print("Default data workflow loaded successfully")
            else:
                print("Default data workflow file not found")
        
        return result
        
    except Exception as e:
        print(f"Error getting default workflows: {str(e)}")
        return {"success": False, "message": f"Error getting default workflows: {str(e)}"}

@router.post("/reset")
async def reset_settings():
    """Reset all settings to default"""
    try:
        default_settings = {
            "workflow_settings": {
                "default_workflow_id": None,
                "default_data_workflow_id": None
            }
        }
        
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": "Settings reset to default"}
    except Exception as e:
        return {"success": False, "message": f"Error resetting settings: {str(e)}"}

@router.delete("/clear_default_workflows")
async def clear_default_workflows():
    """Clear default workflow settings"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Clear workflow settings
        settings["workflow_settings"] = {
            "default_workflow_id": None,
            "default_data_workflow_id": None
        }
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": "Default workflows cleared"}
    except Exception as e:
        return {"success": False, "message": f"Error clearing default workflows: {str(e)}"}