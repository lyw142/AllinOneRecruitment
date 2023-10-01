"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
# from models import db, 
from models import Staff_Skill, db, Staff, Role, Staff, Skill, RoleSkillMapping, RoleListing
from sqlalchemy import desc
from flask import Flask
from flask_cors import CORS
api = Blueprint('api', __name__)



@api.route("/createjoblisting", methods=['POST'])
def createListing():
    data = request.get_json()
    
    # Check if the Role_Name already exists in the database
    existing_role = Role.query.filter_by(Role_Name=data['Role_Name']).first()
    
    if existing_role:
        # Create a new RoleListing entry for the existing role
        role_listing = RoleListing(
            Deadline=data['Deadline'],
            Date_Posted=data['Date_Posted'],
            Hiring_Manager=data['Hiring_Manager'],
            Role_ID=existing_role.Role_ID  # Use the existing role's ID
        )
        db.session.add(role_listing)
        db.session.commit()
        
        return jsonify({"message": "Role already exists, new listing created."}), 200  # HTTP 200 OK status code
    else:
        new_role = Role(
            Role_Name=data['Role_Name'],
            Role_Responsibilities=data['Role_Responsibilities'],
            Role_Requirements=data['Role_Requirements'],
            Salary=data['Salary'],
            Dept=data['Dept']
        )
        
        db.session.add(new_role)
        db.session.commit()

        new_role = Role.query.filter_by(Role_Name=data['Role_Name']).first()
        
        # Query the Skill table to get the Skill_ID for the given Skill_Name
        skill = Skill.query.filter_by(Skill_Name=data['Skill']).first()

        if skill:
            skill_id = skill.Skill_ID
        else:
            # Create a new Skill object if the Skill_Name does not exist in the database
            new_skill = Skill(
                Skill_Name=data['Skill'],
                Skill_Status = "Active"
            )
            db.session.add(new_skill)
            db.session.commit()

            # Retrieve the new Skill_ID
            skill_id = Skill.query.filter_by(Skill_Name=data['Skill']).first().Skill_ID

        new_role_skill = RoleSkillMapping(
            Skill_ID=skill_id,
            Role_ID=new_role.Role_ID
        )
        db.session.add(new_role_skill)
        db.session.commit()

        # Create a new RoleListing entry
        role_listing = RoleListing(
            Deadline=data['Deadline'],
            Date_Posted=data['Date_Posted'],
            Hiring_Manager=data['Hiring_Manager'],
            Role_ID=new_role.Role_ID
        )
        db.session.add(role_listing)
        db.session.commit()

        
        return jsonify({"message": "Role created successfully, Role_SKill mapped and New Listing created."}), 201  # HTTP 201 Created status code


    #  OLD CODE   
    # ----------------------------------------------
    # try:
    #     # Parse the JSON data from the request
    #     data = request.get_json()

    #     # Extract data from the JSON request
    #     deadline = data['Deadline']
    #     date_posted = data['Date_Posted']
    #     hiring_manager_id = data['Hiring_Manager']
    #     role_id = data['Role_ID']

    #     # Check if the Role and Hiring Manager exist
    #     role = Role.query.get(role_id)
    #     if not role:
    #         return jsonify({"message": "Role not found"}), 404

    #     # Create a new RoleListing object
    #     listing = RoleListing(
    #         Deadline=deadline,
    #         Date_Posted=date_posted,
    #         Hiring_Manager=hiring_manager_id,
    #         Role_ID=role_id
    #     )

    #     # Add the new listing to the database session and commit
    #     db.session.add(listing)
    #     db.session.commit()

    #     # Return a success message
    #     return jsonify({"message": "Role listing created successfully"}), 201

    # except Exception as e:
    #     # Handle any exceptions that may occur during the process
    #     db.session.rollback()  # Rollback the transaction in case of an error
    #     return jsonify({"message": "Error creating role listing", "error": str(e)}), 500



@api.route("/openjoblistings")
def findAllOpenJobListings():
    current_date = datetime.now()

    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities, Role.Role_Requirements, Role.Salary)
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .filter(RoleListing.Deadline >= current_date)  # Filter by Deadline
        .order_by(desc(RoleListing.Date_Posted))
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    role_listings_json = []
    for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities, role_requirements, salary in results:
        role_listing_data = {
            "Listing_ID": role_listing.Listing_ID,
            "Deadline": str(role_listing.Deadline),
            "Date_Posted": str(role_listing.Date_Posted),
            "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilities,
            "Role_Requirements": role_requirements,
            "Salary": salary,
            "Skills": retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
        }
        role_listings_json.append(role_listing_data)

    return jsonify(role_listings_json)

def retrieveAllSkillsFromRoleListing(Role_ID):
    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleSkillMapping, Skill.Skill_Name)
        .join(Role, RoleSkillMapping.Role_ID == Role.Role_ID)
        .join(Skill, RoleSkillMapping.Skill_ID == Skill.Skill_ID)
        .filter(Role.Role_ID == Role_ID)
    )

    # Execute the query and retrieve the results
    results = query.all()
    print(results)

    # Convert the results into a JSON format
    skills_json = []
    for skills_name in results:
        skills_json.append(skills_name.Skill_Name)

    return skills_json

@api.route("/getRoleListing/<int:listing_id>")
def getRoleListing(listing_id):
    try:
        # Perform joins to retrieve role listings with Hiring Manager and Role Name for the specified Listing_ID
        query = (
            db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities, Role.Role_Requirements, Role.Salary)
            .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
            .join(Role, RoleListing.Role_ID == Role.Role_ID)
            .filter(RoleListing.Listing_ID == listing_id)  # Filter by the specified Listing_ID
            .order_by(desc(RoleListing.Date_Posted))
        )

        # Execute the query and retrieve the results
        results = query.all()

        # Convert the results into a JSON format
        role_listings_json = []
        for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities, role_requirements, salary in results:
            role_listing_data = {
                "Listing_ID": role_listing.Listing_ID,
                "Deadline": str(role_listing.Deadline),
                "Date_Posted": str(role_listing.Date_Posted),
                "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
                "Role_Name": role_name,
                "Role_Responsibilities": role_responsibilities,
                "Role_Requirements": role_requirements,
                "Salary": salary,
                "Skills": retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
            }
            role_listings_json.append(role_listing_data)

        return jsonify(role_listings_json)

    except Exception as e:
        return jsonify({"message": "Error retrieving role listings", "error": str(e)}), 500

@api.route("/updateRoleListing/<int:listing_id>", methods=["POST"])
def updateRoleListing(listing_id):
    try:
        # Retrieve the role listing based on listing_id
        role_listing = RoleListing.query.get(listing_id)

        if not role_listing:
            return jsonify({"message": "Role listing not found"}), 404

        # Get the JSON data from the request
        data = request.get_json()

        # Update the role listing attributes
        role_listing.Deadline = data["Deadline"]

        # Fetch the corresponding Role object
        role = Role.query.get(role_listing.Role_ID)

        # Update the Role attributes
        if role:
            role.Role_Responsibilities = data["Role_Responsibilities"]
            role.Role_Requirements = data["Role_Requirements"]
        else:
            # Handle the case where the corresponding Role is not found
            return jsonify({"message": "Role not found"}), 404

        # Commit changes to the database
        db.session.commit()

        return jsonify({"message": "Role listing updated successfully"})

    except Exception as e:
        return jsonify({"message": "Error updating role listing", "error": str(e)}), 500

# filter and show closed listings
@api.route("/closedjoblistings")
def findClosedJobListings():
    current_date = datetime.now()

    # Perform joins to retrieve role listings with Hiring Manager and Role Name
    query = (
        db.session.query(RoleListing, Staff.Staff_FName, Staff.Staff_LName, Role.Role_Name, Role.Role_Responsibilities, Role.Role_Requirements, Role.Salary)
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .filter(RoleListing.Deadline < current_date)  # Filter by Deadline smaller than current date
        .order_by(desc(RoleListing.Date_Posted))
    )

    # Execute the query and retrieve the results
    results = query.all()

    # Convert the results into a JSON format
    role_listings_json = []
    for role_listing, hiring_manager_fname, hiring_manager_lname, role_name, role_responsibilities, role_requirements, salary in results:
        role_listing_data = {
            "Listing_ID": role_listing.Listing_ID,
            "Deadline": str(role_listing.Deadline),
            "Date_Posted": str(role_listing.Date_Posted),
            "Hiring_Manager": hiring_manager_fname + " " + hiring_manager_lname,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilities,
            "Role_Requirements": role_requirements,
            "Salary": salary,
            "Skills": retrieveAllSkillsFromRoleListing(role_listing.Role_ID)
        }
        role_listings_json.append(role_listing_data)

    return jsonify(role_listings_json)

#skills api endpoint (clement)
@api.route("/skills", methods=['GET'])  # Define a new endpoint for retrieving skills
def getSkills():
    try:
        # Query the database to retrieve all skills
        skills = Skill.query.all()

        # Convert the skills to a list of dictionaries
        skills_data = [{"Skill_ID": skill.Skill_ID, "Skill_Name": skill.Skill_Name, "Skill_Status": skill.Skill_Status} for skill in skills]

        # Return the skills as JSON response
        return jsonify(skills_data), 200

    except Exception as e:
        return jsonify({"message": "Error retrieving skills", "error": str(e)}), 500

#filter by skills

@api.route("/filterRoleListingBySkill/<list_of_skill_id>")
def filterRoleListingBySkill(list_of_skill_id):
    
    selected_skill_ids = list_of_skill_id.split(',')
    
    subquery = (
        db.session.query(RoleSkillMapping.Role_ID)
        .filter(RoleSkillMapping.Skill_ID.in_(selected_skill_ids))
        .group_by(RoleSkillMapping.Role_ID)
        .having(db.func.count(RoleSkillMapping.Skill_ID.distinct()) == len(selected_skill_ids))
        .subquery()
    )

    # Query the RoleListing table to find role listings based on the subquery
    role_listings = (
        db.session.query(
            RoleListing.Listing_ID,
            RoleListing.Deadline,
            RoleListing.Date_Posted,
            RoleListing.Role_ID,
            db.func.concat(Staff.Staff_FName, " ", Staff.Staff_LName).label("Hiring_Manager_Name"),
            Role.Role_Name,
            Role.Role_Responsibilities,
            Role.Role_Requirements,
            Role.Salary,
        )
        .join(Staff, RoleListing.Hiring_Manager == Staff.Staff_ID)
        .join(Role, RoleListing.Role_ID == Role.Role_ID)
        .join(subquery, RoleListing.Role_ID == subquery.c.Role_ID)
        .order_by(db.desc(RoleListing.Date_Posted))
        .all()
    )


    # Convert the query results into JSON format
    role_listings_json = []

    for role_listing, deadline, date_posted, role_id, hiring_manager_name, role_name, role_responsibilites, role_requirements, salary in role_listings:
        role_listing_data = {
            "Listing_ID": role_listing,
            "Deadline": str(deadline),
            "Date_Posted": str(date_posted),
            "Hiring_Manager": hiring_manager_name,
            "Role_Name": role_name,
            "Role_Responsibilities": role_responsibilites,
            "Role_Requirements" : role_requirements,
            "Salary": salary,
            "Skills": retrieveAllSkillsFromRoleListing(role_id)
        }
        role_listings_json.append(role_listing_data)

    # Return the JSON response
    return jsonify(role_listings_json)

# @api.route("/filterRoleListingBySkills", methods=["POST"])
# def filter_role_listing_by_skills():
#     # Get the selected skills from the request
#     selected_skills = request.json.get("selectedSkills", [])

#     # Filter role listings based on selected skills
#     filtered_listings = [listing for listing in role_listings if all(skill in listing["Skills"] for skill in selected_skills)]

#     # Convert the filtered listings into a JSON format
#     role_listings_json = []
#     for listing in filtered_listings:
#         role_listing_data = {
#             "Listing_ID": listing["Listing_ID"],
#             "Deadline": listing["Deadline"].strftime("%Y-%m-%d"),
#             "Date_Posted": listing["Date_Posted"].strftime("%Y-%m-%d"),
#             "Hiring_Manager": listing["Hiring_Manager"],
#             "Role_Name": listing["Role_Name"],
#             "Role_Responsibilities": listing["Role_Responsibilities"],
#             "Role_Requirements": listing["Role_Requirements"],
#             "Salary": listing["Salary"],
#             "Skills": listing["Skills"],
#         }
#         role_listings_json.append(role_listing_data)

#     return jsonify(role_listings_json)

@api.route("/getStaffSkills/<int:staff_id>")
def getStaffSkills(staff_id):
    try:
        query = (
            db.session.query(Staff_Skill, Skill.Skill_Name)
            .join(Skill, Staff_Skill.Skill_ID == Skill.Skill_ID)
            .filter(Staff_Skill.Staff_ID == staff_id) 
        )

        # Execute the query and retrieve the results
        results = query.all()

        # Convert the results into a JSON format
        staff_json = []

        for staff_skill, skill_name in results:
            staff_skill_data = {
                "Skill_ID": staff_skill.Skill_ID,
                "Skill_Name": skill_name,
            }
            staff_json.append(staff_skill_data)

        return jsonify(staff_json)

    except Exception as e:
        return jsonify({"message": "Error retrieving Staff's Skill", "error": str(e)}), 500
