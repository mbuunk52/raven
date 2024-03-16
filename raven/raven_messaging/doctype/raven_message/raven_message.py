# Copyright (c) 2023, The Commit Company and contributors
# For license information, please see license.txt
import datetime

import frappe
from frappe import _
from frappe.core.utils import html2text
from frappe.model.document import Document

from raven.api.raven_message import track_visit


class RavenMessage(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from raven.raven_messaging.doctype.raven_mention.raven_mention import RavenMention

		channel_id: DF.Link
		content: DF.LongText | None
		file: DF.Attach | None
		file_thumbnail: DF.Attach | None
		image_height: DF.Data | None
		image_width: DF.Data | None
		is_edited: DF.Check
		is_reply: DF.Check
		json: DF.JSON | None
		link_doctype: DF.Link | None
		link_document: DF.DynamicLink | None
		linked_message: DF.Link | None
		mentions: DF.Table[RavenMention]
		message_reactions: DF.JSON | None
		message_type: DF.Literal["Text", "Image", "File"]
		replied_message_details: DF.JSON | None
		text: DF.LongText | None
		thumbnail_height: DF.Data | None
		thumbnail_width: DF.Data | None
	# end: auto-generated types

	def before_validate(self):
		try:
			if self.text:
				content = html2text(self.text)
				# Remove trailing new line characters and white spaces
				self.content = content.rstrip()
		except Exception:
			pass

		if not self.is_new():
			# this is not a new message, so it's a previous message being edited
			old_doc = self.get_doc_before_save()
			if old_doc.text != self.text:
				self.is_edited = True

		self.process_mentions()

	def validate(self):
		"""
		1. If there is a linked message, the linked message should be in the same channel
		"""
		self.validate_linked_message()

	def validate_linked_message(self):
		"""
		If there is a linked message, the linked message should be in the same channel
		"""
		if self.linked_message:
			if frappe.db.get_value("Raven Message", self.linked_message, "channel_id") != self.channel_id:
				frappe.throw(_("Linked message should be in the same channel"))

	def before_insert(self):
		"""
		If the message is a reply, update the replied_message_details field
		"""
		if self.is_reply and self.linked_message:
			details = frappe.db.get_value(
				"Raven Message",
				self.linked_message,
				["text", "content", "file", "message_type", "owner", "creation"],
				as_dict=True,
			)
			self.replied_message_details = {
				"text": details.text,
				"content": details.content,
				"file": details.file,
				"message_type": details.message_type,
				"owner": details.owner,
				"creation": datetime.datetime.strftime(details.creation, "%Y-%m-%d %H:%M:%S"),
			}

	def after_insert(self):

		# // nosemgrep This event needs to be published to all users on Raven
		frappe.publish_realtime(
			"raven:unread_channel_count_updated",
			{
				"channel_id": self.channel_id,
				"play_sound": True,
				"sent_by": self.owner,
			},
		)  # nosemgrep

	def process_mentions(self):
		if not self.json:
			return

		try:
			content = self.json.get("content", [{}])[0].get("content", [])
		except (IndexError, AttributeError):
			return

		entered_ids = set()
		for item in content:
			if item.get("type") == "userMention":
				user_id = item.get("attrs", {}).get("id")
				if user_id and user_id not in entered_ids:
					self.append("mentions", {"user": user_id})
					entered_ids.add(user_id)
					self.send_notification_for_mentions(user_id)

	def send_notification_for_mentions(self, user):
		try:
			from frappe.push_notification import PushNotification

			push_notification = PushNotification("raven")

			if push_notification.is_enabled():
				push_notification.send_notification_to_user(
					user,
					"You were mentioned",
					self.content
					# icon=f"{frappe.utils.get_url()}/assets/hrms/manifest/favicon-196.png",
				)
		except ImportError:
			# push notifications are not supported in the current framework version
			pass
		except Exception:
			frappe.log_error(frappe.get_traceback())

	def after_delete(self):
		frappe.publish_realtime(
			"message_deleted",
			{
				"channel_id": self.channel_id,
				"sender": frappe.session.user,
				"message_id": self.name,
			},
			doctype="Raven Channel",
			# Adding this to automatically add the room for the event via Frappe
			docname=self.channel_id,
		)

	def on_update(self):
		if self.is_edited:
			frappe.publish_realtime(
				"message_edited",
				{
					"channel_id": self.channel_id,
					"sender": frappe.session.user,
					"message_id": self.name,
					"message_details": {
						"text": self.text,
						"content": self.content,
						"file": self.file,
						"message_type": self.message_type,
						"is_edited": 1 if self.is_edited else 0,
						"is_reply": self.is_reply,
						"modified": self.modified,
						"linked_message": self.linked_message,
						"replied_message_details": self.replied_message_details,
						"link_doctype": self.link_doctype,
						"link_document": self.link_document,
						"message_reactions": self.message_reactions,
					},
				},
				doctype="Raven Channel",
				# Adding this to automatically add the room for the event via Frappe
				docname=self.channel_id,
			)
		else:
			frappe.publish_realtime(
				"message_created",
				{
					"channel_id": self.channel_id,
					"sender": frappe.session.user,
					"message_id": self.name,
					"message_details": {
						"text": self.text,
						"content": self.content,
						"file": self.file,
						"message_type": self.message_type,
						"is_edited": 1 if self.is_edited else 0,
						"is_reply": self.is_reply,
						"creation": self.creation,
						"owner": self.owner,
						"modified_by": self.modified_by,
						"modified": self.modified,
						"linked_message": self.linked_message,
						"replied_message_details": self.replied_message_details,
						"link_doctype": self.link_doctype,
						"link_document": self.link_document,
						"message_reactions": self.message_reactions,
						"thumbnail_width": self.thumbnail_width,
						"thumbnail_height": self.thumbnail_height,
						"file_thumbnail": self.file_thumbnail,
						"image_width": self.image_width,
						"image_height": self.image_height,
						"name": self.name,
					},
				},
				doctype="Raven Channel",
				# Adding this to automatically add the room for the event via Frappe
				docname=self.channel_id,
			)

	def on_trash(self):
		# delete all the reactions for the message
		frappe.db.delete("Raven Message Reaction", {"message": self.name})

	def before_save(self):
		# TODO: Remove this
		if frappe.get_cached_value(
			"Raven Channel", self.channel_id, "type"
		) != "Private" or frappe.db.exists(
			"Raven Channel Member",
			{"channel_id": self.channel_id, "user_id": frappe.session.user},
		):
			track_visit(self.channel_id)


def on_doctype_update():
	"""
	Add indexes to Raven Message table
	"""
	# Index the selector (channel or message type) first for faster queries (less rows to sort in the next step)
	frappe.db.add_index("Raven Message", ["channel_id", "creation"])
	frappe.db.add_index("Raven Message", ["message_type", "creation"])
