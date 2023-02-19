import io
import csv
from .gnupg_encrypt import encrypt_with_gnupg


class CSVRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        fout = io.StringIO()
        writer = csv.writer(
            fout, delimiter=';', quoting=csv.QUOTE_ALL)

        writer.writerow(value['header'])
        writer.writerows(value['rows'])

        resp = system['request'].response
        resp.content_type = 'text/csv'
        resp.content_disposition = 'attachment;filename="yes.csv"'
        if system['request'].registry.settings[
                'c3smembership.runmode'] == 'dev':
            return fout.getvalue()
        if system['request'].registry.settings[
                'c3smembership.runmode'] == 'prod':
            return encrypt_with_gnupg(fout.getvalue())
