-- Hajime: aspecto de nvim sobre la paleta de Ryoku (ryoku.lua sigue siendo dueno de los colores).
return {
  {
    "folke/tokyonight.nvim",
    opts = {
      styles = {
        comments = { italic = true },
        keywords = { italic = true },
        sidebars = "dark",
        floats = "dark",
      },
      on_highlights = function(hl, c)
        local border = { fg = c.blue, bg = c.bg }
        hl.FloatBorder = border
        hl.WinSeparator = { fg = c.fg_gutter, bg = c.bg }
        hl.CursorLine = { bg = c.bg_highlight }
        hl.ColorColumn = { bg = c.bg_highlight }
        hl.SnacksPickerBorder = border
        hl.WhichKeyBorder = border
      end,
    },
  },

  -- statusline: git/diagnostics/lsp, rounded sections
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      opts.options = vim.tbl_deep_extend("force", opts.options or {}, {
        theme = "auto",
        globalstatus = true,
        component_separators = { left = "", right = "" },
        section_separators = { left = "\u{e0b4}", right = "\u{e0b6}" },
      })
    end,
  },

  -- tabline with LSP diagnostics and rounded look
  {
    "akinsho/bufferline.nvim",
    opts = {
      options = {
        separator_style = "thin",
        always_show_bufferline = true,
        show_buffer_close_icons = false,
        show_close_icon = false,
        offsets = {
          { filetype = "snacks_layout_box" },
        },
      },
    },
  },

  -- rainbow brackets: helps a lot in Java/Rust/TS nesting
  {
    "HiPhish/rainbow-delimiters.nvim",
    event = "LazyFile",
    main = "rainbow-delimiters.setup",
  },

  -- floating UI polish
  {
    "folke/noice.nvim",
    opts = {
      presets = { lsp_doc_border = true, bottom_search = true, command_palette = true },
    },
  },
  {
    "folke/which-key.nvim",
    opts = { preset = "modern", win = { border = "rounded" } },
  },
  {
    "folke/snacks.nvim",
    opts = {
      indent = { animate = { enabled = false } },
      scroll = { enabled = true },
      explorer = { enabled = true },
      picker = { sources = { explorer = { hidden = true, ignored = false } } },
    },
  },

  -- tree-sitter: solo parsers genericos; los de cada lenguaje los anade el usuario
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      vim.list_extend(opts.ensure_installed or {}, {
        "bash", "json", "lua", "markdown", "markdown_inline", "regex", "toml",
        "vim", "vimdoc", "yaml", "gitcommit",
      })
    end,
  },
}
