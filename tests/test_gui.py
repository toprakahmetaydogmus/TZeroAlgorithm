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
            
            # Verify cycling through all 6 tabs
            for i in range(6):
                app.switch_tab(i)
                root.update()
                
            self.assertEqual(len(app.tab_frames), 6)
        finally:
            try:
                root.destroy()
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
