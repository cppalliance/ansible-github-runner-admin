GitHub Self-Hosted Runner Admin
=========

[Philips Labs Terraform module for scalable self hosted GitHub action runners](https://github.com/philips-labs/terraform-aws-github-runner) launches and manages Github Actions self-hosted runners.

This repository offers an add-on solution in conjunction with the Philips terraform module, to switch runners on and off, either automatically or manually. The main use-case would be to switch between 
GitHub-hosted runners when billing minutes are available, and self-hosted runners after billing minutes are depleted. This Ansible role installs a web server and accompanying scripts to host a central administrative control panel.  

Background
----------

The Philips terraform module launches Github Actions self-hosted runners. The usual way to send GitHub workflow jobs to either GitHub-hosted runners or self-hosted runners is to specify a 'runs-on' label. Certain labels cause the jobs to be processed by self-hosted runners. This is usually stable and consistent. The same jobs are always processed in the same way.

How could you dynamically switch the 'runs-on' labels from a central administration console?

When GitHub runners are slow or busy, you could decide to use self-hosted runners. In addition to a manual setting, the central console could query the GitHub API, and determine if all the billing minutes have been consumed.  At that time, automatically switch to self-hosted runners.

There are two main parts of the puzzle:  

1. In the workflow files themselves such as `.github/workflows/ci.yml` include certain Actions to modify the `runs-on` variable. See https://github.com/cppalliance/aws-hosted-runners for details about this Action and how to incorporate it into your `.github/workflows/workflow.yml` files. What that Action does is query a webserver, which will respond with either a `true` or `false` indicating if self-hosted runners ought to be used or not.  If `true`, the aws-hosted-runners Action sets the labels to choose self-hosted runners.  

2. The webserver mentioned in the previous step could be a very simple mechanism having a webpage that publishes `true` or `false`.  In that case, you only need a basic way to send a textfile with that info.  However, we'd like to incorporate scripts that query the GitHub API and make a more automated decision when to enable or disable self-hosted runners.  This Ansible role installs those scripts along with the webserver.  

Requirements
------------

Ubuntu 22.04. Other package requirements will be installed.  

Installation Instructions
--------------

Review https://github.com/cppalliance/aws-hosted-runners to see the modifications that must be done in the `.github/workflows/` files. Fork or clone that repo into your organization. Follow the README.md there to update your workflow files in multiple GitHub repositories.  

This repository `github-runner-admin` is an Ansible role. Install it on a server, preferably a small dedicated cloud instance which is only used for this function.

All the variables in `defaults/main.yml` may be customized using host_vars, group_vars, or playbook variables. Consider each variable in `defaults/main.yml`.

The role will install a cron script that runs every 30 minutes and queries the GitHub API. The `github_runner_admin_api_token` variable should be set to a token that has API access to billing.  

The nginx vhost is built from `templates/vhost.j2`. After installing, you may compare the vhost to the template, adjust variables as necessary, and re-run ansible.  

`htpasswd_credentials` is an array of usernames/passwords to add in an htpasswd file, giving access to the admin console.  

This role doesn't install Prometheus and Grafana, but it does provide Prometheus data in /var/lib/node_exporter which allows you to graph interesting information about the number of runners and the billing minutes. Therefore, installing Prometheus and Grafana is recommended. See dashboard https://grafana.com/grafana/dashboards/19316-gha-runners/  

Usage Instructions
-------------------

Update multiple workflow files, as covered in https://github.com/cppalliance/aws-hosted-runners.  

Log into the administration console which you installed with this Ansible Role. Use the credentials from the `htpasswd_credentials` variable just mentioned, and navigate to /admin/index.php.  

On that page, you may Enabled, Disable, and Lock the self-hosted runners so they will always (or never) be used.  

The expected method of operating is that the cron script will run every 30 minutes and automatically Enable or Disable the runners.  

If you Lock the setting in the admin panel, that overrides the script, and keeps your setting intact. That way, you may "permanently" disable or enable self-hosted runners if you choose.  

Example Playbook
----------------

There is an example playbook in `playbooks/github_runner_admin.yml`.  
In the ansible inventory, add your server to the `github_runner_admin` group and run the playbook.  

Other Notes
-----------

[scripts/update_workflow.py](scripts/update_workflow.py) is an optional python script to update your GitHub Actions workflow files. Modify as needed. 

License
-------

Boost

Author Information
------------------

CPPAlliance
