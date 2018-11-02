#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default, build_shared

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=True)

    shared_option_name = "%s:shared" % build_shared.get_name_from_recipe()

    filtered_builds = []
    for settings, options, env_vars, build_requires, reference in builder.items:
        if settings["compiler"] == "Visual Studio":
            if shared_option_name in options:
                if options[shared_option_name]:
                    filtered_options = dict(options)
                    del filtered_options[shared_option_name]
                    filtered_builds.append([settings, filtered_options, env_vars, build_requires])
                continue
        filtered_builds.append([settings, options, env_vars, build_requires])
    builder.builds = filtered_builds

    builder.run()
