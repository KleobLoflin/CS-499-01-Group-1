# class: MovementSystem

from game.world.components import Transform, Intent, Movement, Facing, Attack
from game.core.config import Config

class MovementSystem:
    def update(self, world, dt: float) -> None:
        # loops through all entities that have transform and Intent components
        # and adjusts the transform values according to intent and movespeed
        for _, components in world.query(Transform, Intent, Movement, Facing, Attack):
            tr: Transform = components[Transform]
            it: Intent = components[Intent]
            mv: Movement = components[Movement]
            face: Facing = components[Facing]
            atk: Attack = components[Attack]

            # dash ##################################################################################
            # reset cooldown and duration if dash is flagged, we are not attacking, and the cooldown is done
            if it.dash and mv.dash_cooldown == 0.0 and not atk.active:
                mv.dash_cooldown = mv.dash_max_cooldown
                mv.dash_duration = mv.dash_max_duration
                it.dash = False

            # run dash cooldown
            if mv.dash_cooldown > 0.0:
                mv.dash_cooldown = max(0.0, mv.dash_cooldown - dt)
            
            if mv.dash_duration > 0.0:
                mv.dash_duration = max(0.0, mv.dash_duration - dt)

            # write to transform ##################################################################
            # when we are not attacking
            if not atk.active:
                
                # normalize diagonal movement
                if it.move_x and it.move_y:
                    inv = 0.70710678118
                    it.move_x *= inv; it.move_y *= inv

                # movement 
                if mv.dash_duration > 0.0:
                    # Dash applies high speed while active
                    tr.x += it.move_x * mv.dash_speed * dt
                    tr.y += it.move_y * mv.dash_speed * dt
                else:
                    tr.x += it.move_x * mv.speed * dt 
                    tr.y += it.move_y * mv.speed * dt

                # Facing ###########################################################
                face.direction = it.facing
                

#  def handle_event(self, event) -> None:
#         if event.type == pygame.KEYDOWN:
#             if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
#                 if self.dash_cooldown <= 0.0 and self.dash_timer <= 0.0:
#                     keys = pygame.key.get_pressed()
#                     dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
#                     dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])

#                     if dx or dy:
#                         # Normalize diagonal
#                         if dx and dy:
#                             inv = 0.70710678118
#                             dx *= inv; dy *= inv

#                         self.dash_dir = (dx, dy)
#                         self.dash_timer = Config.DASH_DURATION  
#                         self.dash_cooldown = Config.DASH_COOLDOWN  

#     def update(self, world, dt: float) -> None:
#         intent: Intent = world.get(self.player_id, Intent)
#         if intent is None:
#             return

#         # Decrement timers
#         if self.dash_timer > 0.0:
#             self.dash_timer -= dt
#         if self.dash_cooldown > 0.0:
#             self.dash_cooldown -= dt

#         # Movement input
#         keys = pygame.key.get_pressed()
#         dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
#         dy = (keys[pygame.K_s] or keys[pygame.K_DOWN])  - (keys[pygame.K_w] or keys[pygame.K_UP])

#         if dx and dy:
#             inv = 0.70710678118
#             dx *= inv; dy *= inv

#         # Normal movement
#         intent.move_x = float(dx)
#         intent.move_y = float(dy)

#         # Dash movement overrides normal move
#         if self.dash_timer > 0.0:
#             intent.dash_x = self.dash_dir[0]
#             intent.dash_y = self.dash_dir[1]
#         else:
#             intent.dash_x = 0.0
#             intent.dash_y = 0.0

#         # attacking
#         if not intent.basic_atk:
#             if keys[pygame.K_SPACE]:
#                 intent.basic_atk = True