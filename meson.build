project('gllvm-meson', 'c')

gclang = find_program('gclang', required: false)
gclang_cpp = find_program('gclang++', required: false)
get_bc = find_program('get-bc', required: false)
gclang_is_wllvm = false
if not gclang.found() or not gclang_cpp.found()
  gclang = find_program('wllvm', required: false)
  gclang_cpp = find_program('wllvm++', required: false)
  get_bc = find_program('extract-bc', required: false)
  gclang_is_wllvm = true
  if not gclang.found() or not gclang_cpp.found()
    # note: we need a gllvm version after commit fa0b9ea
    error('Neither gllvm nor wllvm found. One of them is required. Install gllvm with `go install github.com/SRI-CSL/gllvm/cmd/...@master` (and put ~/go/bin/ into your path).')
  endif
endif

summary({
  'Found gclang/wllvm': gclang.full_path(),
  'Found gclang++/wllvm++': gclang_cpp.full_path(),
  'Found get-bc': get_bc.full_path(),
  'Use wllvm instead of gllvm': gclang_is_wllvm,
}, bool_yn: true)

build_tools_env = environment()
build_tools_env.set('PYTHONPATH', meson.current_source_dir())
