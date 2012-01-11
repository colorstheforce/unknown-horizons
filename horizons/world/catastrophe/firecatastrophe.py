# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from horizons.world.catastrophe import Catastrophe
from horizons.world.status import SettlerUnhappyStatus
from horizons.constants import GAME_SPEED
from horizons.constants import BUILDINGS
from horizons.command.building import Tear
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback

class FireCatastrophe(Catastrophe):

	SEED_CHANCE = 0.2

	EXPANSION_TIME = GAME_SPEED.TICKS_PER_SECOND * 10

	EXPANSION_RADIUS = 2

	# Defines the mininum number of settler buildings that need to be in a
	# settlement before this catastrophe can break loose
	MIN_SETTLERS_FOR_BREAKOUT = 5

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 30

	def __init__(self, settlement, manager):
		super(FireCatastrophe, self).__init__(settlement, manager)
		self._affected_buildings = []

	def breakout(self):
		possible_buildings = self._settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS)
		if len(possible_buildings) == 0:
			return False
		choice = self._settlement.session.random.randint(0, len(possible_buildings)-1)
		building = possible_buildings[choice]
		self.infect(building)
		return True

	@classmethod
	def can_breakout(cls, settlement):
		return len(settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS)) > cls.MIN_SETTLERS_FOR_BREAKOUT

	def expand(self):
		if not self.evaluate():
			self._manager.end_catastrophe(self._settlement)
			# We are done here, time to leave
			return
		for building in self._affected_buildings:
			for tile in self._settlement.get_tiles_in_radius(building.position, self.EXPANSION_RADIUS, False):
				if tile.object is not None and tile.object.id == BUILDINGS.RESIDENTIAL_CLASS and tile.object not in self._affected_buildings:
					if self._settlement.session.random.random() <= self.SEED_CHANCE:
						self.infect(tile.object)
						return

	def end(self):
		Scheduler().rem_all_classinst_calls(self)

	def infect(self, building):
		"""Infect a building with fire"""
		building._registered_status_icons.append(SettlerUnhappyStatus())
		self._affected_buildings.append(building)
		Scheduler().add_new_object(Callback(self.wreak_havoc, building), self, run_in = self.TIME_BEFORE_HAVOC)

	def evaluate(self):
		return len(self._affected_buildings) > 0

	def wreak_havoc(self, building):
		self._affected_buildings.remove(building)
		Tear(building).execute(self._settlement.session)