
import datetime
import pprint
from os import environ

import jwt
import pydantic
from api.controllers.student import field_update_controller
from api.drivers.student import student_drivers
from api.middlewares import authentication_middleware
from api.models.student import student_model
from api.repository import student_repo, student_skills_repo
from api.schemas.student.request_schemas import student_request_schemas
from api.utils.exceptions import exceptions
from api.utils.factory import student_factory
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def construct_router():

    student = APIRouter(
        tags=["Student"]
    )

    @student.post("/login", status_code=status.HTTP_200_OK)
    async def login(request: Request):
        """Handles student login."""

        try:
            request = await request.json()

            jwt_payload = jwt.encode(
                {
                    "token" : request["user_id"],
                    "role" : "student",
                    "exp": datetime.datetime.now(tz=datetime.timezone.utc) + 
                            datetime.timedelta(days = int(environ.get("JWT_EXP", 1)))
                },
                environ.get("SECRET_KEY"),
                algorithm=environ.get("JWT_ALGORITHM")
            )

            response = student_repo.update_refresh_token(request["user_id"])

            if not response:
                return JSONResponse(
                    status_code=500,
                    content = {
                        "message" : "internal server error"
                    }
                )
            
            refresh_token = jwt.encode(
                {
                    "user_id" : request["user_id"],
                    "role" : "student",
                    "refresh_token" : response,
                    "exp": datetime.datetime.now(tz=datetime.timezone.utc) + 
                            datetime.timedelta(days = int(environ.get("JWT_EXP", 1)))
                },
                environ.get("SECRET_KEY"),
                algorithm=environ.get("JWT_ALGORITHM")
            )

            return JSONResponse(
                status_code=200,
                content = {
                    "token" : jwt_payload,
                    "refresh_token" : refresh_token
                }
            )

        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content = {
                    "message" : "internal server error"
                }
            )


    @student.post("/add")
    async def add_student(request: student_request_schemas.RegisterStudentSchema):
        #TODO: Optimise and clean the code
        try:

            student = student_drivers.Student()

            response = await student.add_student(request)
            
            message = "student created"

            return JSONResponse(
                status_code=status.HTTP_201_CREATED, 
                content=message
            )

        except exceptions.UnexpectedError as e:
            #TODO: log to logger

            return JSONResponse(
                status_code=500,
                content="unexpected error occured"
            )

        except exceptions.DuplicateStudent as e:
            #TODO: log to logger

            return JSONResponse(
                status_code=409,
                content="student already exists"
            )

    
    @student.post("/activate")
    async def activate_student_account(
        request: Request,
        authorization = Depends(authentication_middleware.is_authenticated)):
        
        request = await request.json()

        response = await student_repo.verify_student_handler(request, authorization)

        return response


    @student.post("/add/skills")
    async def add_skills(request: Request):
        
        request = await request.json()

        response = await student_skills_repo.add_skills_handler(request["skills"])

        return response


    return student
