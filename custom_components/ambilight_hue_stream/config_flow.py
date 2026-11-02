"""Config flow: pair with the TV (PIN), link the Hue bridge (button), pick the entertainment area."""

from __future__ import annotations

import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from . import api
from .const import (
    CONF_ADB,
    CONF_ENT_ID,
    CONF_HUE_APPID,
    CONF_HUE_CLIENTKEY,
    CONF_HUE_HOST,
    CONF_HUE_USER,
    CONF_TV_HOST,
    CONF_TV_PASS,
    CONF_TV_USER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AmbiHueConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._pairing: dict | None = None
        self._areas: dict[str, str] = {}

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            self._data.update(user_input)
            try:
                self._pairing = await self.hass.async_add_executor_job(api.tv_pair_request, user_input[CONF_TV_HOST])
            except (api.ApiError, requests.RequestException) as exc:
                _LOGGER.warning("TV pairing request failed: %s", exc)
                errors["base"] = "tv_unreachable"
            else:
                return await self.async_step_tv_pin()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TV_HOST, default=self._data.get(CONF_TV_HOST, "")): str,
                    vol.Required(CONF_HUE_HOST, default=self._data.get(CONF_HUE_HOST, "")): str,
                    vol.Required(CONF_ADB, default=True): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_tv_pin(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            try:
                user, password = await self.hass.async_add_executor_job(
                    api.tv_pair_grant, self._data[CONF_TV_HOST], self._pairing, user_input["pin"].strip()
                )
            except (api.ApiError, requests.RequestException) as exc:
                _LOGGER.warning("TV pairing grant failed: %s", exc)
                errors["base"] = "bad_pin"
            else:
                self._data[CONF_TV_USER], self._data[CONF_TV_PASS] = user, password
                return await self.async_step_hue_link()
        return self.async_show_form(step_id="tv_pin", data_schema=vol.Schema({vol.Required("pin"): str}), errors=errors)

    async def async_step_hue_link(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            try:
                key = await self.hass.async_add_executor_job(api.hue_register, self._data[CONF_HUE_HOST])
            except (api.ApiError, requests.RequestException) as exc:
                _LOGGER.warning("Hue registration failed: %s", exc)
                errors["base"] = "hue_unreachable"
            else:
                if key is None:
                    errors["base"] = "link_button"
                else:
                    self._data[CONF_HUE_USER] = key["username"]
                    self._data[CONF_HUE_CLIENTKEY] = key["clientkey"]
                    self._data[CONF_HUE_APPID] = key["appid"]
                    return await self.async_step_area()
        return self.async_show_form(step_id="hue_link", data_schema=vol.Schema({}), errors=errors)

    async def async_step_area(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            self._data[CONF_ENT_ID] = user_input[CONF_ENT_ID]
            await self.async_set_unique_id(f"{self._data[CONF_TV_HOST]}_{user_input[CONF_ENT_ID]}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=f"Ambilight TV + Hue Sync: {self._areas[user_input[CONF_ENT_ID]]}", data=self._data)
        self._areas = await self.hass.async_add_executor_job(
            api.hue_entertainment_areas, self._data[CONF_HUE_HOST], self._data[CONF_HUE_USER]
        )
        if not self._areas:
            return self.async_abort(reason="no_areas")
        return self.async_show_form(
            step_id="area", data_schema=vol.Schema({vol.Required(CONF_ENT_ID): vol.In(self._areas)})
        )
