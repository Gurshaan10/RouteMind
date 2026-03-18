"""Standardized error responses for API."""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class RouteMindError(HTTPException):
    """Base error class for RouteMind API."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "details": self.details
            }
        )


class CityNotFoundError(RouteMindError):
    """City not found error."""
    def __init__(self, city_id: int):
        super().__init__(
            error_code="CITY_NOT_FOUND",
            message=f"City with ID {city_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"city_id": city_id}
        )


class NoActivitiesError(RouteMindError):
    """No activities found for city."""
    def __init__(self, city_id: int):
        super().__init__(
            error_code="NO_ACTIVITIES_FOUND",
            message=f"No activities found for city ID {city_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"city_id": city_id}
        )


class InvalidDateRangeError(RouteMindError):
    """Invalid date range error."""
    def __init__(self, message: str = "End date must be after start date"):
        super().__init__(
            error_code="INVALID_DATE_RANGE",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidBudgetError(RouteMindError):
    """Invalid budget error."""
    def __init__(self, message: str = "Budget per day must be non-negative"):
        super().__init__(
            error_code="INVALID_BUDGET",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InfeasibleConstraintsError(RouteMindError):
    """Constraints cannot be satisfied."""
    def __init__(self, message: str, infeasible_items: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="INFEASIBLE_CONSTRAINTS",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=infeasible_items or {}
        )


class ValidationError(RouteMindError):
    """General validation error."""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

