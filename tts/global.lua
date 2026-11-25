--[[
Too Many Secrets (v0.52.0) -- Tabletop Simulator Global script.
Generated alongside the save by `python3 -m tts.build_tts`; edit tts/global.lua, not the save.

1. Fit: every object whose GM Notes read "fit:<w>x<d>" is scaled to exactly
   <w> x <d> table units, so card and board images keep their PnP proportions.
2. Cube Tower: the Shogun Baffle model from sim/tower.py (the v0.52.0 preset).
   Cubes stuck on the internal baffles are kept hidden in the script state.
   "Drop Staging Cup" compiles everything in the Staging Cup bag; the cubes that
   exit appear in the Exit Tray area beside the tower.
3. Quick Setup: the 2P / 3P / 4P buttons run RULES.md Section 3 for that many
   seats. SETUP (from the builder) holds the object GUIDs and the table spots,
   computed from the PnP board layout.
4. Dice: every die is a Custom Dice d6 drawn from pnp DICE_SPECS (GM Notes
   "die:<colour>"). Its six rotation values are renamed to the face yields
   (DIE_FACES, from the builder), so rolls and tooltips read e.g. "5: R&D face".
]]

-- __CONFIG__ (replaced by the builder: STAGING_CUP_GUID, TOWER_GUID, TRAY_ORIGIN, CUBE_TEMPLATES, SETUP, DIE_FACES)

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
local setupReport = nil -- set once Quick Setup has run

-- ---------------------------------------------------------------- save/load

function onSave()
  return JSON.encode({ stuck = towerStuck, report = lastReport, setup = setupReport })
end

function onLoad(saved)
  math.randomseed(os.time())
  if saved and saved ~= "" then
    local ok, state = pcall(JSON.decode, saved)
    if ok and state then
      towerStuck = state.stuck or {}
      lastReport = state.report or lastReport
      setupReport = state.setup
    end
  end
  Wait.time(fitAll, 1)
  Wait.time(function()
    setStatus(lastReport)
    if setupReport then showSetupDone(setupReport) end
  end, 0.5)
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

-- Rename a custom die's rotation values ("1".."6") to its face names.
function nameDieFaces(obj)
  if obj == nil or DIE_FACES == nil then return end
  local key = (obj.getGMNotes() or ""):match("die:(%a+)")
  local names = key and DIE_FACES[key]
  if names == nil then return end
  local rv = obj.getRotationValues()
  if rv == nil then return end
  local changed = false
  for _, entry in ipairs(rv) do
    local n = tonumber(entry.value)
    if n and names[n] then
      entry.value = names[n]
      changed = true
    end
  end
  if changed then obj.setRotationValues(rv) end
end

function fitAll()
  for _, obj in ipairs(getObjects()) do
    fitObject(obj)
    nameDieFaces(obj)
  end
end

-- Cards drawn from a deck keep the card's own fit; dice drawn from a bag get their face names.
function onObjectLeaveContainer(container, obj)
  Wait.frames(function() fitObject(obj); nameDieFaces(obj) end, 2)
end

function onObjectSpawn(obj)
  Wait.frames(function() fitObject(obj); nameDieFaces(obj) end, 2)
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

-- Setup drop: 1 Red, 1 Blue, 1 Green, 1 Black into the empty tower. Returns false if not empty.
function primeCompiler()
  if #towerStuck > 0 then
    broadcastToAll("Cube Tower: already primed (the tower is not empty).", { 1, 0.8, 0.4 })
    return false
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
  return true
end

function uiPrime(player)
  primeCompiler()
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

-- ---------------------------------------------------------------- quick setup

local SETUP_Y = 2.2      -- drop height for objects placed by Quick Setup

local function at(p, y) return { p[1], y or SETUP_Y, p[2] } end

local function byGuid(guid)
  if guid == nil then return nil end
  return getObjectFromGUID(guid)
end

local function moveTo(guid, p, rotY, y)
  local o = byGuid(guid)
  if o == nil then return nil end
  o.setPositionSmooth(at(p, y), false, true)
  if rotY then o.setRotationSmooth({ 0, rotY, 0 }, false, true) end
  return o
end

-- Top card of a deck, face up at p. A deck down to one card is a Card object.
local function dealTop(guid, p, rotY, shuffle)
  local d = byGuid(guid)
  if d == nil then return nil end
  if d.type == "Card" then
    d.setPositionSmooth(at(p), false, true)
    d.setRotationSmooth({ 0, rotY, 0 }, false, true)
    return d
  end
  if shuffle then d.shuffle() end
  return d.takeObject({ position = at(p), rotation = { 0, rotY, 0 }, smooth = true })
end

-- Shuffle a deck and return the names of its top n cards (the cards dealMany will deal).
local function shuffleAndPeek(guid, n)
  local d = byGuid(guid)
  if d == nil then return {} end
  if d.type == "Card" then return { d.getName() } end
  d.shuffle()
  local names = {}
  for i, entry in ipairs(d.getObjects()) do
    if i > n then break end
    names[i] = entry.name
  end
  return names
end

-- Deal the top cards of a deck, one per spot.
local function dealMany(guid, spots, rotYs)
  local d = byGuid(guid)
  for i, p in ipairs(spots) do
    if d == nil then return end
    if d.type == "Card" then
      d.setPositionSmooth(at(p), false, true)
      d.setRotationSmooth({ 0, rotYs[i], 0 }, false, true)
      return
    end
    d.takeObject({ position = at(p), rotation = { 0, rotYs[i], 0 }, smooth = true })
    if d.remainder then d = d.remainder end
  end
end

local function takeFromBag(guid, p, rotY, y, onSpawn)
  local bag = byGuid(guid)
  if bag == nil then return nil end
  return bag.takeObject({
    position = at(p, y), rotation = { 0, rotY or 180, 0 }, smooth = false,
    callback_function = onSpawn,
  })
end

-- Seats to fill: the seated colours if exactly n of them sit at a mat, else the first n mats.
local function chooseSeats(n)
  local seated = {}
  for i, s in ipairs(SETUP.seats) do
    if Player[s.color] and Player[s.color].seated then table.insert(seated, i) end
  end
  if #seated == n then return seated end
  local list = {}
  for i = 1, n do list[i] = i end
  return list
end

local function spawnTokens(bagKey, p, count, rotY, y0)
  for i = 1, count do
    takeFromBag(SETUP.token_bags[bagKey], p, rotY, (y0 or SETUP_Y) + i * 0.25)
  end
end

function showSetupDone(text)
  UI.setAttribute("setupButtons", "active", "false")
  UI.setAttribute("setupStatus", "text", text)
end

function quickSetup(player, n)
  if setupReport then
    broadcastToAll("Quick Setup has already run in this game.", { 1, 0.8, 0.4 })
    return
  end
  local seats = chooseSeats(n)

  -- 1. SETEC Roadmap: 1 tile per Version, Active Version Marker on v1.0, prime, starting cubes.
  local v1 = nil
  for _, ver in ipairs({ "v1.0", "v2.0", "v3.0" }) do
    local tile = dealTop(SETUP.version_decks[ver], SETUP.version_slots[ver], 180, true)
    if ver == "v1.0" then v1 = tile end
  end
  local v1Name = v1 and v1.getName() or "?"
  moveTo(SETUP.version_marker, SETUP.version_marker_spot, 180, SETUP_Y + 0.4)
  primeCompiler()
  local cup = byGuid(STAGING_CUP_GUID)
  local cupSpot = SETUP.staging_cup_spot
  local payload = SETUP.payload[v1Name] or {}
  local k = 0
  for _, color in ipairs({ "Red", "Blue", "Green", "Black" }) do
    for _ = 1, (payload[color] or 0) do
      k = k + 1
      takeFromBag(SETUP.cube_bags[color], cupSpot, 180, 4 + k * 0.5, function(o)
        if cup then cup.putObject(o) end
      end)
    end
  end
  local secrets = SETUP.start.secrets + (SETUP.secret_bonus[v1Name] or 0)

  -- 2. Client Company + White Hat Dossier per player (without replacement). The cards
  --    land where the player's dice and cubes start, so they are dealt once those
  --    have moved onto the mat (step 5).
  local companySpots, whiteHatSpots, rots = {}, {}, {}
  for i, si in ipairs(seats) do
    local s = SETUP.seats[si]
    companySpots[i], whiteHatSpots[i], rots[i] = s.spots.company, s.spots.white_hat, s.rot
  end
  local companies = shuffleAndPeek(SETUP.company_deck, n)
  local whiteHats = shuffleAndPeek(SETUP.white_hat_deck, n)

  -- 3. Software Market: 1 Variant card per colour with 2 x players dice beside it; each
  --    player's starting colored die comes off its colour's stack.
  local wantColor = {}
  local lines = {}
  for i, si in ipairs(seats) do
    local cname = companies[i] or "?"
    wantColor[i] = SETUP.company_die[cname]
    local wname = whiteHats[i] or "?"
    table.insert(lines, string.format("%s: %s / %s (%s die)", SETUP.seats[si].color, cname, wname,
      wantColor[i] or "?"))
  end
  for _, color in ipairs({ "Red", "Blue", "Green", "Yellow" }) do
    local slot = SETUP.variant_slots[color]
    dealTop(SETUP.variant_decks[color], slot, 180, true)
    local onCard = 2 * n
    for i, si in ipairs(seats) do
      if wantColor[i] == color then
        onCard = onCard - 1
        local s = SETUP.seats[si]
        takeFromBag(SETUP.market_bags[color], s.spots.ready[3], s.rot, SETUP_Y, function(o)
          o.setName(color .. " die (Client Company)")
        end)
      end
    end
    for d = 1, onCard do
      local off = SETUP.market_dice_grid[d]
      takeFromBag(SETUP.market_bags[color], { slot[1] + off[1], slot[2] + off[2] }, 180, SETUP_Y + 0.6)
    end
  end

  -- 4. Each Company Terminal Mat: dice, track cubes at Level 0, markers, starting tokens.
  local share = SETUP.start.share[tostring(n)]
  -- Market Share Markers start as one stack: the First Player's marker on top, then
  -- each next player clockwise beneath it. SETUP.seats runs counter-clockwise (White,
  -- Pink, Teal, Orange), so clockwise means stepping back through that list.
  local firstIdx = math.random(#seats)
  local ring = #SETUP.seats
  for k, si in ipairs(seats) do
    local rank = (seats[firstIdx] - si) % ring      -- clockwise steps from the First Player
    SETUP.seats[si].stackRank = rank
  end
  local ranks = {}
  for _, si in ipairs(seats) do table.insert(ranks, SETUP.seats[si].stackRank) end
  table.sort(ranks)                                  -- 0 = First Player (top of the stack)
  for _, si in ipairs(seats) do
    local s = SETUP.seats[si]
    for pos, r in ipairs(ranks) do
      if r == s.stackRank then s.stackY = SETUP_Y + (#seats - pos + 1) * 0.6 end
    end
  end
  for _, si in ipairs(seats) do
    local s = SETUP.seats[si]
    local sp, dice, cubes = s.spots, s.dice, s.cubes
    moveTo(dice.ready[1], sp.ready[1])
    moveTo(dice.ready[2], sp.ready[2])
    moveTo(dice.purple, sp.ready[4])
    for j, guid in ipairs(dice.sprint) do moveTo(guid, sp.sprint[j]) end
    moveTo(dice.reserve, sp.reserve)
    for _, key in ipairs({ "pen", "triage", "release", "pr" }) do moveTo(cubes[key], sp[key]) end
    moveTo(cubes.sig, sp.sig)
    moveTo(cubes.override, sp.override)
    moveTo(cubes.vuln, sp.vuln)
    moveTo(cubes.share, sp.share[tostring(share)], nil, s.stackY)
    spawnTokens("secret", sp.secret, secrets, s.rot)
    spawnTokens("money5", sp.money, math.floor(SETUP.start.money / 5), s.rot)
    spawnTokens("money1", sp.money, SETUP.start.money % 5, s.rot, SETUP_Y + 1.0)
  end

  -- 2 players: the SETEC Corp Black Cube on 0 on the Central Market Share Track.
  if n == 2 then
    takeFromBag(SETUP.cube_bags.Black, SETUP.setec_share_spot, 180, SETUP_Y, function(o)
      o.setName("SETEC Corp Black Cube")
      o.setDescription("2 players: ranks on the Central Market Share Track; starts on 0.")
    end)
  end

  -- 5. Deal the Client Company and White Hat Dossier cards beside the mats.
  Wait.time(function()
    dealMany(SETUP.company_deck, companySpots, rots)
    dealMany(SETUP.white_hat_deck, whiteHatSpots, rots)
  end, 1.5)

  -- 6. First Player Marker (the player whose Market Share Marker is on top).
  local first = SETUP.seats[seats[firstIdx]]
  moveTo(SETUP.first_player, first.spots.first_player, first.rot, SETUP_Y + 0.4)

  local who = (player and player.steam_name) or "A player"
  local summary = string.format("Quick Setup (%dP) by %s. v1.0: %s (%d Secrets each). Market Share %d. First player: %s.\n%s",
    n, who, v1Name, secrets, share, first.color, table.concat(lines, "\n"))
  broadcastToAll(summary, { 0.85, 1, 0.85 })
  setupReport = string.format("%dP set up. First player: %s.", n, first.color)
  showSetupDone(setupReport)
end

function uiSetup2(player) quickSetup(player, 2) end
function uiSetup3(player) quickSetup(player, 3) end
function uiSetup4(player) quickSetup(player, 4) end
