from app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')  # host='0.0.0.0' for ngrok accessibility