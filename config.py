class Config:
    SECRET_KEY = 'your_secret_key'  # Replace with a secure random string
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost:3306/car_pooling_system'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
