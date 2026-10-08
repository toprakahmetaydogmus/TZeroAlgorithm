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
            self.assertIn("Choose a workspace folder", app.tree_empty_lbl.cget("text"))
            self.assertEqual(app.header_search_entry.get(), "Search files...")
            self.assertTrue(root.bind("<Control-k>"))

            app.scanned_files = ["src/app.py", "README.md"]
            app.file_sizes = {"src/app.py": 128, "README.md": 64}
            app.file_snippets = {"src/app.py": "def app(): pass", "README.md": "# App"}
            app.file_checked = {"src/app.py": True, "README.md": False}
            app.has_scanned = True
            app.header_search_entry.delete(0, "end")
            app.header_search_entry.insert(0, "app.py")
            app._submit_header_search()

            self.assertEqual(app.active_tab_index, 1)
            self.assertTrue(app.tree.exists("src/app.py"))
            self.assertFalse(app.tree.exists("README.md"))

            original_target = app.dir_entry.get()
            app._rebuild_layout_for_theme("Glass Dark")
            self.assertEqual(app.dir_entry.get(), original_target)
            self.assertEqual(app.search_entry.get(), "app.py")
            self.assertTrue(app.tree.exists("src/app.py"))
            self.assertFalse(app.tree.exists("README.md"))
            self.assertIn("1 / 2 selected", app.selector_stats_lbl.cget("text"))
            
            # Verify cycling through all tabs
            for i in range(len(app.tab_frames)):
                app.switch_tab(i)
                root.update()
                
            self.assertEqual(len(app.tab_frames), 7)
            app.scanned_files = []
            app.file_checked = {}
            app.rebuild_selector_tree()
            self.assertIn("No supported source files found", app.tree_empty_lbl.cget("text"))
        finally:
            try:
                root.destroy()
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
