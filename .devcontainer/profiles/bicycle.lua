-- .devcontainer/profiles/bicycle.lua
-- Bicycle profile for OSRM (estratto dal repo project-osrm/osrm-backend @v5.27)

api_version = 4

-- routing options
local find_access_tag = require('lib/access').find_access_tag
local measure_distance = require('lib/measure').measure_distance
local limit_weight = require('lib/debug').limit_weight
local utils = require('lib/utils')

properties.max_speed_for_map_matching      = 110/3.6 -- 110kmph -> m/s
properties.weight_name                     = 'cyclability'
properties.weight_precision                = 1
properties.mode                            = mode.cycling
properties.traffic_signal_penalty          = 2
properties.u_turn_penalty                  = 2
properties.turn_penalty                    = 30
properties.turn_bias                       = 1.1

-- default speeds (km/h)
local default_speeds = {
  cycleway = 18,
  primary = 22,
  secondary = 18,
  tertiary = 18,
  residential = 18,
  service = 15,
  track = 12,
  path = 12,
  living_street = 12,
  unclassified = 12,
}

-- surface speed factors
local surface_speeds = {
  asphalt = 1.0,
  concrete = 1.0,
  paving_stones = 0.9,
  compacted = 0.9,
  fine_gravel = 0.8,
  gravel = 0.7,
  dirt = 0.5,
  ground = 0.5,
  grass = 0.5,
  sand = 0.4,
}

-- barriers that completely block cycling
local barriers = {
  bollard = true,
  gate = true,
  lift_gate = true,
  yes = true,
  turnstile = true,
}

-- access tags hierarchy
local access_tag_whitelist = {
  yes = true,
  designated = true,
  permissive = true,
}

local access_tag_blacklist = {
  no = true,
  private = true,
  dismount = true,
}

-- *****************************************************************
-- Node handler
-- *****************************************************************
function node_function(node, result)
  local barrier = node:get_value_by_key('barrier')
  if barriers[barrier] then
    result.barrier = true
  end
end

-- *****************************************************************
-- Way handler
-- *****************************************************************
function way_function(way, result)

  local highway = way:get_value_by_key('highway')
  if not highway then
    return
  end

  -- access
  local access = find_access_tag(way, access_tag_whitelist, access_tag_blacklist)
  if access and access_tag_blacklist[access] then
    return
  end

  -- surface
  local surface = way:get_value_by_key('surface')
  local surface_factor = surface_speeds[surface] or 1.0

  -- speed
  local speed = default_speeds[highway] or 12
  speed = speed * surface_factor
  result.forward_speed = speed
  result.backward_speed = speed

  -- mode
  result.forward_mode = mode.cycling
  result.backward_mode = mode.cycling

  -- name
  local name = way:get_value_by_key('name') or way:get_value_by_key('ref')
  if name then
    result.name = name
  end

  -- weight (cyclability = time)
  result.weight = measure_distance(way) / (speed * 1000/3600) -- seconds
end
