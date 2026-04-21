"""
amoginarium/logic/entities/_new_groups/_logic_group.py

Project: amoginarium
Created: 21.04.2026
Authors: LukasKrah
"""

class LogicGroup:
    def __init__(self, *sprites):
        self.spritedict = {}
        self.lostsprites = []

        self.add(*sprites)

    def sprites(self):
        return list(self.spritedict)

    def add_internal(
        self,
        sprite,
        layer=None,  # noqa pylint: disable=unused-argument; supporting legacy derived classes that override in non-pythonic way
    ):
        """
        For adding a sprite to this group internally.

        :param sprite: The sprite we are adding.
        :param layer: the layer to add to, if the group type supports layers
        """
        self.spritedict[sprite] = None

    def remove_internal(self, sprite):
        """
        For removing a sprite from this group internally.

        :param sprite: The sprite we are removing.
        """
        if lost_rect := self.spritedict[sprite]:
            self.lostsprites.append(lost_rect)
        del self.spritedict[sprite]

    def has_internal(self, sprite):
        """
        For checking if a sprite is in this group internally.

        :param sprite: The sprite we are checking.
        """
        return sprite in self.spritedict

    def copy(self):
        """copy a group with all the same sprites

        Group.copy(): return Group

        Returns a copy of the group that is an instance of the same class
        and has the same sprites in it.

        """
        return self.__class__(  # noqa pylint: disable=too-many-function-args
            self.sprites()  # Needed because copy() won't work on AbstractGroup
        )

    def __iter__(self):
        return iter(self.sprites())

    def __contains__(self, sprite):
        return self.has(sprite)

    def add(self, *sprites):
        """add sprite(s) to group

        Group.add(sprite, list, group, ...): return None

        Adds a sprite or sequence of sprites to a group.

        """
        for sprite in sprites:
            # It's possible that some sprite is also an iterator.
            # If this is the case, we should add the sprite itself,
            # and not the iterator object.
            if not self.has_internal(sprite):
                self.add_internal(sprite)
                sprite.add_internal(self)

    def remove(self, *sprites):
        """remove sprite(s) from group

        Group.remove(sprite, list, or group, ...): return None

        Removes a sprite or sequence of sprites from a group.

        """
        # This function behaves essentially the same as Group.add. It first
        # tries to handle each argument as an instance of the Sprite class. If
        # that fails, then it tries to handle the argument as an iterable
        # object. If that fails, then it tries to handle the argument as an
        # old-style sprite group. Lastly, if that fails, it assumes that the
        # normal Sprite methods should be used.
        for sprite in sprites:
            if self.has_internal(sprite):
                self.remove_internal(sprite)
                sprite.remove_internal(self)

    def has(self, *sprites):
        """ask if group has a sprite or sprites

        Group.has(sprite or group, ...): return bool

        Returns True if the given sprite or sprites are contained in the
        group. Alternatively, you can get the same information using the
        'in' operator, e.g. 'sprite in group', 'subgroup in group'.

        """
        if not sprites:
            return False  # return False if no sprites passed in

        for sprite in sprites:
            if not self.has_internal(sprite):
                return False

        return True

    def update(self, *args, **kwargs):
        """call the update method of every member sprite

        Group.update(*args, **kwargs): return None

        Calls the update method of every member sprite. All arguments that
        were passed to this method are passed to the Sprite update function.

        """
        for sprite in self.sprites():
            sprite.update(*args, **kwargs)

    def draw(self, surface, bgd=None, special_flags=0):  # noqa pylint: disable=unused-argument; bgd arg used in LayeredDirty
        """draw all sprites onto the surface

        Group.draw(surface, bgd=None, special_flags=0): return Rect_list

        Draws all of the member sprites onto the given surface.

        """
        sprites = self.sprites()
        if hasattr(surface, "blits"):
            self.spritedict.update(
                zip(
                    sprites,
                    surface.blits(
                        (spr.image, spr.rect, None, special_flags) for spr in sprites
                    ),
                )
            )
        else:
            for spr in sprites:
                self.spritedict[spr] = surface.blit(
                    spr.image, spr.rect, None, special_flags
                )
        self.lostsprites = []
        dirty = self.lostsprites

        return dirty

    def clear(self, surface, bgd):
        """erase the previous position of all sprites

        Group.clear(surface, bgd): return None

        Clears the area under every drawn sprite in the group. The bgd
        argument should be Surface which is the same dimensions as the
        screen surface. The bgd could also be a function which accepts
        the given surface and the area to be cleared as arguments.

        """
        if callable(bgd):
            for lost_clear_rect in self.lostsprites:
                bgd(surface, lost_clear_rect)
            for clear_rect in self.spritedict.values():
                if clear_rect:
                    bgd(surface, clear_rect)
        else:
            surface_blit = surface.blit
            for lost_clear_rect in self.lostsprites:
                surface_blit(bgd, lost_clear_rect, lost_clear_rect)
            for clear_rect in self.spritedict.values():
                if clear_rect:
                    surface_blit(bgd, clear_rect, clear_rect)

    def empty(self):
        """remove all sprites

        Group.empty(): return None

        Removes all the sprites from the group.

        """
        for sprite in self.sprites():
            self.remove_internal(sprite)
            sprite.remove_internal(self)

    def __bool__(self):
        return bool(self.sprites())

    def __len__(self):
        """return number of sprites in group

        Group.len(group): return int

        Returns the number of sprites contained in the group.

        """
        return len(self.sprites())

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"
