import os

from factory import db
from server.model import Member, SeasonalPreference

class AIDatabaseClient:
    def __init__(self):
        self.methods = {
            'request_address': self.get_santee_address,
            'request_wishlist': self.get_santee_wishlist,
            'process_my_address': self.write_my_address,
            'process_my_wishlist': self.write_my_wishlist,
            'remind_my_address': self.get_my_address,
            'remind_my_wishlist': self.get_my_wishlist,
            'remind_my_santee': self.get_santee_id,
        }

    # @staticmethod
    def get_santee_address(self, member_id):
        """
        Get the address for a member's santee.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The address of the member's santee.
        """
        santee_id = self.get_santee_id(member_id)
        member = (
            db.session.query(Member)
            .filter(Member.id == santee_id)
            .one()
        )
        return member.address
    
    # @staticmethod
    def get_santee_wishlist(self, member_id):
        """
        Get the wishlist for a member's santee.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The wishlist of the member's santee.
        """
        santee_id = self.get_santee_id(member_id)
        seasonal_preference = (
            db.session.query(SeasonalPreference)
            .filter(SeasonalPreference.member_id == santee_id)
            .one()
        )
        return seasonal_preference.wishlist

    # @staticmethod
    def get_my_address(self, member_id):
        """
        Get the address for a member.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The address of the member.
        """
        member = (
            db.session.query(Member)
            .filter(Member.id == member_id)
            .one()
        )
        return member.address
    
    # @staticmethod
    def get_my_wishlist(self, member_id):
        """
        Get the wishlist for a member.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The wishlist of the member.
        """
        seasonal_preference = (
            db.session.query(SeasonalPreference)
            .filter(SeasonalPreference.member_id == member_id)
            .one()
        )
        return seasonal_preference.wishlist
    
    # @staticmethod
    def get_my_santee_name(self, member_id):
        """
        Get the name for a member's santee.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The name of the member's santee.
        """
        santee_id = self.get_santee_id(member_id)
        member = (
            db.session.query(Member)
            .filter(Member.id == santee_id)
            .one()
        )
        return member.name
    
    def get_my_santa_details(self, member_id):
        """
        Get the details for a member's santa.

        Args:
            member_id (int): The ID of the member.

        Returns:
            dict: The details of the member's santa.
        """
        seasonal_preference = (
            db.session.query(SeasonalPreference)
            .filter(SeasonalPreference.secret_santee_id == member_id)
            .one()
        )
        santa_member = (
            db.session.query(Member)
            .filter(Member.id == seasonal_preference.member_id)
            .one()
        )
        return {
            'id': santa_member.id,
            'name': santa_member.name,
            'address': santa_member.address,
            'phone': santa_member.phone,
        }

    def get_my_santee_details(self, member_id):
        """
        Get the details for a member's santee.

        Args:
            member_id (int): The ID of the member.

        Returns:
            dict: The details of the member's santee.
        """
        santee_id = self.get_santee_id(member_id)
        member = (
            db.session.query(Member)
            .filter(Member.id == santee_id)
            .one()
        )
        return {
            'id': member.id,
            'name': member.name,
            'address': member.address,
            'phone': member.phone,
        }
    
    # @staticmethod
    def get_santee_id(self, member_id):
        """
        Get the ID for the secret santee of a member.

        Args:
            member_id (int): The ID of the member.

        Returns:
            str: The ID of the member's secret santee.
        """
        try:
            seasonal_preference = (
                db.session.query(SeasonalPreference)
                .filter(SeasonalPreference.member_id == member_id)
                .one()
            )
            return seasonal_preference.secret_santee_id
        except Exception as e:
            print('error getting santee id', e)
            raise e
    
    # @staticmethod
    def write_my_address(self, member_id, address):
        """
        Write the address for a member.

        Args:
            member_id (int): The ID of the member.
            address (str): The address of the member.
        """
        try:
            member = (
                db.session.query(Member)
                .filter(Member.id == member_id)
                .one()
            )
            member.address = address
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('unable save member address', e)
            raise e
    
    # @staticmethod
    def write_my_wishlist(self, member_id, wishlist):
        """
        Write the wishlist for a member.

        Args:
            member_id (int): The ID of the member.
            wishlist (str): The wishlist of the member.
        """
        try:
            seasonal_preference = (
                db.session.query(SeasonalPreference)
                .filter(SeasonalPreference.member_id == member_id)
                .one()
            )
            seasonal_preference.wishlist = wishlist
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('unable save member wishlist', e)
            raise e