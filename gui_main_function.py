def main():
    """Main function to initialize and run the GUI application."""
    app = Application(sys.argv)
    app.setApplicationName("Crew GUI")
    app.setApplicationVersion("1.0")

    # Set application icon if available
    icon_path = Path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Create and show the main window
    window = CrewGUI()
    window.show()

    # Start the event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
