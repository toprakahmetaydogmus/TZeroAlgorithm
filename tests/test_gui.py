"""
Test GUI Instantiation and Tab Switching
Safely skipped if running in a headless CI container without DISPLAY.
"""
import unittest
import os

class TestGUIInstantiation(unittest.TestCase):
    def test_gui_initialization_and_tabs(self):
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
        except Exception as e:
            raise unittest.SkipTest(f"Tkinter display not available: {e}")
        
        try:
            from tzero_v3 import AutoReadmeGUI
            app = AutoReadmeGUI(root)
            self.assertIsNotNone(app)
            self.assertIsNotNone(app.console_text)
            
            # Verify cycling through all tabs
            for i in range(len(app.tab_frames)):
                app.switch_tab(i)
                root.update()
                
            self.assertEqual(len(app.tab_frames), 7)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
