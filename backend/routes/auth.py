from flask import request,Blueprint
from models.auth import User
from models.company import Company
from extension import db
from werkzeug.security import(generate_password_hash,check_password_hash)
from flask_jwt_extended import(create_access_token,jwt_required,get_jwt_identity)

auth_bp = Blueprint(
    "auth",__name__
)


@auth_bp.route("/register",  methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    existing_user = User.query.filter_by(
        email=data["email"]
    ).first()

    if existing_user:
        return {
            "message": "Email already exists"
        }, 400
    
    allowed_roles = ["student","company"]
    if role not in allowed_roles:
        return{
            "message": "invalid role"
        }, 400
    
    hashed_password = generate_password_hash(data["password"])

    # company ko pehle admin approve karega
    is_blocked = True if role == "company" else False

    new_user = User(
        name = name,
        email = email,
        password = hashed_password,
        role = role,
        is_blocked = is_blocked
    )
    db.session.add(new_user)
    db.session.flush()

    if role == "company":
        db.session.add(Company(
            user_id=new_user.id,
            company_name=name,
            description=(data.get("description") or "")
        ))

    db.session.commit()

    if role == "company":
        return {"message": "Registration successful! Please wait for admin approval."}, 201
    return {"message": "Registered successfully!"}, 201



@auth_bp.route("/login",methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(
        email = email
    ).first()
    if not user:
        return {"message":"user not found"}
    
    if not check_password_hash(
        user.password,
        password
    ):
        return {"message": "Wrong password"}, 401

    if user.is_blocked:
        message = (
            "Your account is pending admin approval. Please wait."
            if user.role == "company"
            else "Your account has been deactivated by admin."
        )
        return {"message": message}, 403

    access_token = create_access_token(
        identity=str(user.id)
    )

    return {
        "message": "Login successful",
        "token": access_token,
        "role": user.role
    }, 200
    
