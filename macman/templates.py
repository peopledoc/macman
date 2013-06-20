import os


def generate_vagrantfile(template, vagrantfile, context={}):
    """Write vagrantfile from template against context."""
    if not os.path.exists(os.path.dirname(vagrantfile)):
        os.makedirs(os.path.dirname(vagrantfile))
    template_content = open(template).read()
    output_content = template_content % context
    with open(vagrantfile, 'w') as output_file:
        output_file.write(output_content)
