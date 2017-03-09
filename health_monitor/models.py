"""
   Copyright 2017 Gracenote

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from django.db import models
from django.utils import timezone
from jsonfield import JSONField

from health_monitor import utils


class Health(models.Model):
    uid = models.IntegerField(unique=True, db_index=True, verbose_name="UID")
    state = JSONField(default={}, blank=True, null=True)
    severity = JSONField(default={}, blank=True, null=True)
    change_date = models.DateTimeField(default=None, blank=True, null=True)

    def __unicode__(self):      # For Python 2, use __str__ on Python 3
        return unicode(self.uid)

    def add_state_group(self, group, test_name):
        """Add state key for group if not present."""
        if group not in self.state.keys():
            self.state[group] = {}
        if test_name not in self.state[group].keys():
            self.state[group][test_name] = {}

    def update_score(self, test_name, score):
        """Update the health based on the test name and score."""
        now = timezone.now()

        for group in utils.get_group_list_for_test(test_name):
            if test_name in utils.get_health_keys(group):
                self.add_state_group(group, test_name)
                self.state[group][test_name]['score'] = score
                self.state[group][test_name]['updated_at'] = now
                self.update_severity(group, test_name)
        self.save()

    def update_severity(self, group, test_name):
        """Set group severity to max of scores."""
        now = timezone.now()
        old_severity = self.severity[group] if group in self.severity.keys() else None
        self.severity[group] = utils.calculate_severity(group, self.state)
        if old_severity != self.severity[group]:
            self.change_date = now
