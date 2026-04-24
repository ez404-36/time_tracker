from PyInstaller.utils.hooks import collect_all

def pre_safe_import_module(api):
	api.add_runtime_task('runtime_suppres_console.py')


def pre_find_modules_path(api):
	pass


def post_find_modules_path(api):
	pass