import tensorflow as tf

print("TensorFlow version:", tf.__version__)

# Load the model
print("Loading model...")
try:
    model = tf.keras.models.load_model("models/mondicare_final.keras")
    print("✅ Model loaded successfully!")
    
    # Re-save it
    print("Re-saving model...")
    model.save("models/mondicare_clean.keras")
    print("✅ Model saved as models/mondicare_clean.keras")
    
except Exception as e:
    print(f"❌ Error: {e}")