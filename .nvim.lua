-- Kartoza Hugo Site - Project-specific Neovim configuration
-- Provides whichkey shortcuts under <leader>p for project tasks

local ok, wk = pcall(require, "which-key")
if not ok then
  vim.notify("which-key not found, skipping project keybindings", vim.log.levels.WARN)
  return
end

-- Helper function to find unreviewed markdown files
local function find_unreviewed_pages()
  local content_dir = vim.fn.getcwd() .. "/content"
  local unreviewed = {}

  -- Use ripgrep to find all markdown files, then filter for those without reviewedBy
  local handle = io.popen('find "' .. content_dir .. '" -name "*.md" -type f 2>/dev/null')
  if not handle then
    return unreviewed
  end

  for file in handle:lines() do
    -- Skip _index.md files (section pages)
    if not file:match("_index%.md$") then
      local f = io.open(file, "r")
      if f then
        local content = f:read("*all")
        f:close()
        -- Check if file has front matter and reviewedBy field
        local front_matter = content:match("^%-%-%-(.-)%-%-%-")
        if front_matter then
          if not front_matter:match("reviewedBy:") then
            table.insert(unreviewed, file)
          end
        end
      end
    end
  end
  handle:close()

  return unreviewed
end

-- Show unreviewed pages in quickfix list
local function show_unreviewed_quickfix()
  local unreviewed = find_unreviewed_pages()
  if #unreviewed == 0 then
    vim.notify("All pages have been reviewed!", vim.log.levels.INFO)
    return
  end

  local qf_list = {}
  for _, file in ipairs(unreviewed) do
    table.insert(qf_list, {
      filename = file,
      lnum = 1,
      text = "Missing reviewedBy in front matter"
    })
  end

  vim.fn.setqflist(qf_list)
  vim.cmd("copen")
  vim.notify(string.format("Found %d unreviewed pages", #unreviewed), vim.log.levels.INFO)
end

-- Open next unreviewed page using Telescope
local function open_unreviewed_telescope()
  local has_telescope, telescope_builtin = pcall(require, "telescope.builtin")
  local unreviewed = find_unreviewed_pages()

  if #unreviewed == 0 then
    vim.notify("All pages have been reviewed!", vim.log.levels.INFO)
    return
  end

  if has_telescope then
    local pickers = require("telescope.pickers")
    local finders = require("telescope.finders")
    local conf = require("telescope.config").values
    local actions = require("telescope.actions")
    local action_state = require("telescope.actions.state")

    pickers.new({}, {
      prompt_title = "Unreviewed Pages (" .. #unreviewed .. " remaining)",
      finder = finders.new_table({
        results = unreviewed,
        entry_maker = function(entry)
          local display = entry:gsub(vim.fn.getcwd() .. "/content/", "")
          return {
            value = entry,
            display = display,
            ordinal = display,
          }
        end,
      }),
      sorter = conf.generic_sorter({}),
      attach_mappings = function(prompt_bufnr, map)
        actions.select_default:replace(function()
          actions.close(prompt_bufnr)
          local selection = action_state.get_selected_entry()
          vim.cmd("edit " .. selection.value)
        end)
        return true
      end,
    }):find()
  else
    -- Fallback to quickfix if telescope not available
    show_unreviewed_quickfix()
  end
end

-- Add reviewedBy to current file
local function add_reviewer_to_current()
  local reviewer = vim.fn.input("Reviewer name: ")
  if reviewer == "" then
    vim.notify("Cancelled - no reviewer name provided", vim.log.levels.WARN)
    return
  end

  local date = os.date("%Y-%m-%d")
  local bufnr = vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)

  -- Find the end of front matter (second ---)
  local front_matter_end = nil
  local dash_count = 0
  for i, line in ipairs(lines) do
    if line:match("^%-%-%-") then
      dash_count = dash_count + 1
      if dash_count == 2 then
        front_matter_end = i
        break
      end
    end
  end

  if front_matter_end then
    -- Insert reviewedBy and reviewedDate before the closing ---
    local insert_line = front_matter_end - 1
    vim.api.nvim_buf_set_lines(bufnr, insert_line, insert_line, false, {
      'reviewedBy: "' .. reviewer .. '"',
      'reviewedDate: ' .. date,
    })
    vim.notify("Added reviewer: " .. reviewer, vim.log.levels.INFO)
  else
    vim.notify("Could not find front matter in this file", vim.log.levels.ERROR)
  end
end

-- Count unreviewed pages
local function count_unreviewed()
  local unreviewed = find_unreviewed_pages()
  vim.notify(string.format("Unreviewed pages: %d", #unreviewed), vim.log.levels.INFO)
end

-- Approve current file (auto-fill with git user name and today's date)
local function approve_current_file()
  -- Get git user name
  local handle = io.popen("git config user.name 2>/dev/null")
  local reviewer = ""
  if handle then
    reviewer = handle:read("*l") or ""
    handle:close()
  end

  if reviewer == "" then
    vim.notify("Could not get git user.name - please configure git", vim.log.levels.ERROR)
    return
  end

  local date = os.date("%Y-%m-%d")
  local bufnr = vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)

  -- Check if file is a markdown file
  local filename = vim.api.nvim_buf_get_name(bufnr)
  if not filename:match("%.md$") then
    vim.notify("Not a markdown file", vim.log.levels.WARN)
    return
  end

  -- Check if already reviewed
  for _, line in ipairs(lines) do
    if line:match("^reviewedBy:") then
      vim.notify("File already has reviewedBy - use 'Add reviewer' to change", vim.log.levels.WARN)
      return
    end
  end

  -- Find the end of front matter (second ---)
  local front_matter_end = nil
  local dash_count = 0
  for i, line in ipairs(lines) do
    if line:match("^%-%-%-") then
      dash_count = dash_count + 1
      if dash_count == 2 then
        front_matter_end = i
        break
      end
    end
  end

  if front_matter_end then
    -- Insert reviewedBy and reviewedDate before the closing ---
    local insert_line = front_matter_end - 1
    vim.api.nvim_buf_set_lines(bufnr, insert_line, insert_line, false, {
      'reviewedBy: "' .. reviewer .. '"',
      'reviewedDate: ' .. date,
    })
    vim.notify("Approved by " .. reviewer .. " on " .. date, vim.log.levels.INFO)
  else
    vim.notify("Could not find front matter in this file", vim.log.levels.ERROR)
  end
end

-- Hugo server commands
local function hugo_serve()
  vim.cmd("!hugo server -D &")
  vim.notify("Hugo server started", vim.log.levels.INFO)
end

local function hugo_build()
  vim.cmd("!hugo")
end

-- Register which-key mappings
wk.add({
  { "<leader>p", group = "Project (Kartoza Hugo)" },

  -- Review management
  { "<leader>pr", group = "Review" },
  { "<leader>prl", open_unreviewed_telescope, desc = "List unreviewed pages" },
  { "<leader>prq", show_unreviewed_quickfix, desc = "Unreviewed to quickfix" },
  { "<leader>prA", approve_current_file, desc = "Approve file (auto)" },
  { "<leader>pra", add_reviewer_to_current, desc = "Add reviewer (manual)" },
  { "<leader>prc", count_unreviewed, desc = "Count unreviewed pages" },

  -- Hugo commands
  { "<leader>ph", group = "Hugo" },
  { "<leader>phs", hugo_serve, desc = "Start Hugo server" },
  { "<leader>phb", hugo_build, desc = "Build site" },

  -- Quick navigation
  { "<leader>pf", group = "Files" },
  { "<leader>pfc", "<cmd>e content/<CR>", desc = "Open content folder" },
  { "<leader>pfl", "<cmd>e layouts/<CR>", desc = "Open layouts folder" },
  { "<leader>pft", "<cmd>e themes/<CR>", desc = "Open themes folder" },
})

vim.notify("Kartoza Hugo project config loaded. Use <leader>p for project commands.", vim.log.levels.INFO)
