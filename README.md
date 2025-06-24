# Amazon Alexa Checkout API

## Overview
This project implements an Amazon Alexa skill that facilitates the checkout process from rental properties/hotels through voice interaction. When the skill’s intent is invoked, it updates a Firestore document to set the building’s status to “checked out” and resets related cleaning flags in subcollections.



## Prerequisites
- **Python**: 3.8 or higher  
- **AWS Account** with Lambda and Alexa Skill permissions  
- **Firebase Project** with Firestore enabled  

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-org/alexa-checkout-api.git
   cd alexa-checkout-api
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** 
   ```bash
   e.g SECRET_KEY='{"type": "service_account", "project_id": "...", … }'
   ```

## Deployment (zip file approach)

1. **Package for AWS Lambda**  
   ```bash
   zip -r checkout_skill.zip checkout.py lambda_function.py
   ```

2. **Upload to Lambda**  
   - In the AWS Lambda console, create a new function or update an existing one.  
   - Upload `checkout_skill.zip`.  
   - Set the handler to `lambda_function.lambda_handler`.  
   - Add environment variables for `SECRET_KEY` and `BUILDING_ID`.

3. **Configure the Alexa Skill**  
   - In the Alexa Developer Console, create or open your skill.  
   - Under “Endpoint,” select AWS Lambda ARN and paste your function’s ARN.  
   - Define the `CheckOutIntent` in your interaction model with sample utterances such as:  
     - “チェックアウトしました”  
     - “Check out building”
    
   Note:  We've deployed our skill using docker

## Usage

- **Launch the Skill**
  Define an invocation name for the skill


- **Trigger Checkout**  
  Using the invocation name trigger the alexa skill

- **Firestore Changes**  
  Upon successful checkout, your changes should be applied in Firebase


