--[[
Too Many Secrets (v0.50.0) -- Tabletop Simulator Global script.
Generated alongside the save by `python3 -m tts.build_tts`; edit tts/global.lua, not the save.

1. Fit: every object whose GM Notes read "fit:<w>x<d>" is scaled to exactly
   <w> x <d> table units, so card and board images keep their PnP proportions.
2. Cube Tower: the Shogun Baffle model from sim/tower.py (the v0.50.0 preset).
   Cubes stuck on the internal baffles are kept hidden in the script state.
   "Drop Staging Cup" compiles everything in the Staging Cup bag; the cubes that
   exit appear in the Exit Tray area beside the tower.
]]

-- __CONFIG__ (replaced by the builder: STAGING_CUP_GUID, TOWER_GUID, TRAY_ORIGIN, CUBE_TEMPLATES)

-- Shogun Baffle physics (GameConfig.v047(): sim/config.py)
local PHYS = {
  empty_exit     = 0.70, -- falling pass-through when the tower is empty
  alpha          = 0.15, -- pass-through lost per stuck cube (trapping regime)
  min_fall       = 0.35, -- floor on falling pass-through (trapping regime)
  trap_dislodge  = 0.21, -- stuck cube knocked loose (trapping regime)
  av_fall        = 0.60, -- falling pass-through (avalanche)
  av_dislodge    = 0.70, -- stuck cube knocked loose (avalanche)
  av_stuck       = 3,    -- S >= 3 triggers avalanche
  av_mass        = 7,    -- F + S >= 7 triggers avalanche
}

local towerStuck = {}   -- object data tables of cubes resting on the baffles
local lastReport = "Tower ready."

-- ---------------------------------------------------------------- save/load

function onSave()
  return JSON.encode({ stuck = towerStuck, report = lastReport })
end

function onLoad(saved)
  math.randomseed(os.time())
  if saved and saved ~= "" then
    local ok, state = pcall(JSON.decode, saved)
    if ok and state then
      towerStuck = state.stuck or {}
      lastReport = state.report or lastReport
    end
  end
  Wait.time(fitAll, 1)
  Wait.time(function() setStatus(lastReport) end, 0.5)
end

-- ---------------------------------------------------------------- fitting

local function parseFit(obj)
  local notes = obj.getGMNotes() or ""
  local w, d = notes:match("fit:([%d%.]+)x([%d%.]+)")
  if not w then return nil end
  return tonumber(w), tonumber(d)
end

function fitObject(obj)
  if obj == nil then return end
  local w, d = parseFit(obj)
  if not w then return end
  local b = obj.getBoundsNormalized()
  if b == nil or b.size.x <= 0.001 or b.size.z <= 0.001 then return end
  local fx, fz = w / b.size.x, d / b.size.z
  if math.abs(fx - 1) > 0.01 or math.abs(fz - 1) > 0.01 then
    local s = obj.getScale()
    obj.setScale({ s.x * fx, s.y, s.z * fz })
  end
end

function fitAll()
  for _, obj in ipairs(getObjects()) do
    fitObject(obj)
  end
end

-- Cards drawn from a deck keep the card's own fit.
function onObjectLeaveContainer(container, obj)
  Wait.frames(function() fitObject(obj) end, 2)
end

function onObjectSpawn(obj)
  Wait.frames(function() fitObject(obj) end, 2)
end

-- ---------------------------------------------------------------- tower

local function shogun(falling, stuck)
  if falling <= 0 then return 0.0, 0.0 end
  if stuck == 0 then return PHYS.empty_exit, 0.0 end
  if stuck >= PHYS.av_stuck or (falling + stuck) >= PHYS.av_mass then
    return PHYS.av_fall, PHYS.av_dislodge
  end
  return math.max(PHYS.min_fall, PHYS.empty_exit - PHYS.alpha * stuck), PHYS.trap_dislodge
end

-- Drops `falling` (object data tables) through the tower; returns the exited list.
local function compile(falling)
  local pFall, pDislodge = shogun(#falling, #towerStuck)
  local exited, newStuck = {}, {}
  if #falling == 0 then return exited end
  for _, data in ipairs(falling) do
    if math.random() < pFall then table.insert(exited, data) else table.insert(newStuck, data) end
  end
  for _, data in ipairs(towerStuck) do
    if math.random() < pDislodge then table.insert(exited, data) else table.insert(newStuck, data) end
  end
  towerStuck = newStuck
  return exited
end

local function summarize(list)
  if #list == 0 then return "nothing" end
  local counts, order = {}, {}
  for _, data in ipairs(list) do
    local name = data.Nickname or data.Name or "Cube"
    if counts[name] == nil then
      counts[name] = 0
      table.insert(order, name)
    end
    counts[name] = counts[name] + 1
  end
  table.sort(order)
  local parts = {}
  for _, name in ipairs(order) do table.insert(parts, counts[name] .. "x " .. name) end
  return table.concat(parts, ", ")
end

local function trayPosition(i)
  local cols = 4
  local col = (i - 1) % cols
  local row = math.floor((i - 1) / cols)
  return { TRAY_ORIGIN[1] + col * 0.75, TRAY_ORIGIN[2] + 1.5 + row * 0.1, TRAY_ORIGIN[3] - row * 0.75 }
end

local function spawnToTray(list)
  for i, data in ipairs(list) do
    data.GUID = nil
    data.Locked = false
    spawnObjectData({ data = data, position = trayPosition(i), rotation = { 0, 180, 0 } })
  end
end

function setStatus(text)
  lastReport = text
  UI.setAttribute("towerStatus", "text", text)
end

function uiDropCup(player)
  local cup = getObjectFromGUID(STAGING_CUP_GUID)
  if cup == nil then
    broadcastToAll("Cube Tower: the Staging Cup bag is missing.", { 1, 0.4, 0.4 })
    return
  end
  local data = cup.getData()
  local falling = data.ContainedObjects or {}
  if #falling > 0 then cup.reset() end
  local exited = compile(falling)
  spawnToTray(exited)
  local who = (player and player.steam_name) or "A player"
  local msg = string.format("Compiler Drop (%s): %d dropped -> exited %s.", who, #falling, summarize(exited))
  if #exited == 0 then
    msg = msg .. " Empty Exit Tray: Compile Buffer Overflow (+1 Red, Blue, Green to the Staging Cup)."
  end
  broadcastToAll(msg, { 0.85, 0.9, 1 })
  setStatus(string.format("Last drop: %d dropped, %d exited.", #falling, #exited))
end

function uiPrime(player)
  if #towerStuck > 0 then
    broadcastToAll("Cube Tower: already primed (the tower is not empty).", { 1, 0.8, 0.4 })
    return
  end
  local falling = {}
  for _, key in ipairs({ "Red", "Blue", "Green", "Black" }) do
    table.insert(falling, JSON.decode(JSON.encode(CUBE_TEMPLATES[key])))
  end
  local exited = compile(falling)
  -- Setup rule: cubes that exit the priming drop return to the general supply.
  local stuckCount = 4 - #exited
  broadcastToAll(string.format(
    "Prime the Compiler: 4 cubes dropped, %d exited back to the supply, %d stuck inside the tower.",
    #exited, stuckCount), { 0.85, 0.9, 1 })
  setStatus(string.format("Primed: %d cube(s) stuck inside.", stuckCount))
end

function uiEmptyTower(player)
  if #towerStuck == 0 then
    broadcastToAll("Cube Tower: the tower is already empty.", { 1, 0.8, 0.4 })
    return
  end
  local list = towerStuck
  towerStuck = {}
  spawnToTray(list)
  broadcastToAll("Cube Tower emptied into the Exit Tray area: " .. summarize(list) .. ".", { 1, 0.8, 0.4 })
  setStatus("Tower emptied.")
end
