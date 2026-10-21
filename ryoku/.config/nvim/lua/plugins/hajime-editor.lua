-- Hajime: ajustes de edicion y fuente de kitty mientras nvim esta abierto.
-- Va como parche de LazyVim.opts (se fusiona) y no como fork de config/options.lua ni
-- config/autocmds.lua, que son de Ryoku y se quedarian congelados.
return {
  {
    "LazyVim/LazyVim",
    opts = function(_, opts)
      local opt = vim.opt
      opt.winborder = "rounded"
      opt.scrolloff = 8
      opt.sidescrolloff = 8
      opt.pumblend = 10
      opt.winblend = 10
      opt.pumheight = 12
      opt.undofile = true
      opt.colorcolumn = "100"
      opt.list = true
      opt.listchars = { tab = "» ", trail = "·", nbsp = "␣" }
      opt.fillchars = { eob = " ", fold = " ", foldopen = "▾", foldclose = "▸", diff = "╱" }
      opt.linebreak = true
      opt.confirm = true

      -- nvim no puede cambiar la fuente del terminal: se lo pide a kitty (allow_remote_control).
      vim.g.hajime_font_size = vim.g.hajime_font_size or 15
      if vim.env.KITTY_WINDOW_ID and not vim.env.TMUX and vim.fn.executable("kitten") == 1 then
        local function set_font(size)
          vim.fn.jobstart({ "kitten", "@", "set-font-size", tostring(size) }, { detach = false })
        end
        local group = vim.api.nvim_create_augroup("hajime-font", { clear = true })
        vim.api.nvim_create_autocmd({ "VimEnter", "VimResume" }, {
          group = group,
          callback = function()
            set_font(vim.g.hajime_font_size)
          end,
        })
        vim.api.nvim_create_autocmd({ "VimLeave", "VimSuspend" }, {
          group = group,
          callback = function()
            vim.fn.system({ "kitten", "@", "set-font-size", "0" })
          end,
        })
        vim.keymap.set("n", "<leader>u+", function()
          vim.g.hajime_font_size = vim.g.hajime_font_size + 1
          set_font(vim.g.hajime_font_size)
        end, { desc = "Font size +" })
        vim.keymap.set("n", "<leader>u-", function()
          vim.g.hajime_font_size = math.max(8, vim.g.hajime_font_size - 1)
          set_font(vim.g.hajime_font_size)
        end, { desc = "Font size -" })
      end
      return opts
    end,
  },
}
