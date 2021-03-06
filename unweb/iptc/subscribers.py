# -*- coding: utf-8 -*-
from dateutil import parser
from iptcinfo import IPTCInfo
from logging import getLogger
from Products.Archetypes.interfaces import IObjectEditedEvent
from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.ATContentTypes.interface import IATImage
from Products.CMFCore.utils import getToolByName
from zope.component import adapter

import os
import tempfile

try:
    from unweb.watermark.extender import ImageExtender
    from unweb.watermark.subscribers import applyWatermark
    WATERMARK = 1
except ImportError:
    WATERMARK = 0

logger = getLogger('unweb.iptc')


@adapter(IATImage, IObjectInitializedEvent)
def readIPTC(obj, event):
    """ Load all the basic IPTC metadata from the Image file and store them in
        the relevant metadata fields (title, description, keywords, creator,
        copyright, creation-date) """
    img = obj.getImage()
    filename = img.getFilename()
    if not filename:
        filename = obj.getId()
    fd, filename = tempfile.mkstemp('_' + filename)
    os.close(fd)
    fout = open(filename, 'wb')
    fout.write(img.data)
    fout.close()

    info = IPTCInfo(filename, force=True)

    title = info.data['object name']
    if title:
        try:
            obj.setTitle(title)
        except UnicodeDecodeError:
            obj.setTitle(title.decode('latin-1'))
        except UnicodeDecodeError:
            obj.setTitle(title.decode('utf-8', 'ignore'))

    description = info.data['caption/abstract']
    if description:
        try:
            obj.setDescription(description)
        except UnicodeDecodeError:
            obj.setDescription(description.decode('utf-8', 'ignore'))

    creator = info.data['by-line']
    if creator:
        try:
            obj.setCreators([creator])
        except UnicodeDecodeError:
            obj.setCreators([creator.decode('utf-8', 'ignore')])

    copyright = info.data['copyright notice']
    if copyright:
        try:
            obj.setRights(copyright)
        except UnicodeDecodeError:
            obj.setRights(copyright.decode('utf-8', 'ignore'))

    keywords = info.data['keywords']
    if keywords:
        try:
            obj.setSubject(keywords)
        except UnicodeDecodeError:
            obj.setSubject([k.decode('utf-8', 'ignore') for k in keywords])

    location = info.data['sub-location'] or ''
    city = info.data['city'] or ''
    state = info.data['province/state'] or ''
    country = info.data['country/primary location name'] or ''
    countryCode = info.data['country/primary location code'] or ''
    if (country or countryCode or state or city or location):
        try:
            obj.setLocation('%s %s %s %s %s' % (country, countryCode, state, city, location))
        except UnicodeDecodeError:
            obj.setLocation('%s %s %s %s %s' % (country.decode('utf-8', 'ignore'), countryCode.decode('utf-8', 'ignore'), state.decode('utf-8', 'ignore'), city.decode('utf-8', 'ignore'), location.decode('utf-8', 'ignore')))

    creation_date = info.data['date created']  # eg '20090820'
    creation_time = info.data['time created']  # eg '112738+0200'
    try:
        if creation_date is not None and creation_time is not None:
            creation_timestamp = '{0} {1}'.format(creation_date, creation_time)
            # created = datetime.strptime(creation_timestamp, '%Y%m%d %H%M%S%z')
            # unfortunately does not work on many systems
            # see http://stackoverflow.com/a/8525115/810427
            created = parser.parse(creation_timestamp)
        else:
            # no iptc creation date+time can be found, use exif creation date
            created = obj.getEXIFOrigDate()

        obj.setCreationDate(created)

    except ValueError:
        logger.warning('Could not parse IPTC creation date for {}'.format(
            '/'.join(obj.getPhysicalPath())))

    obj.reindexObject()


@adapter(IATImage, IObjectEditedEvent)
def updateIPTC(obj, event):
    """ On edit store the updated image metadata inside the image file itself in
        IPTC format """

    if WATERMARK:
        state = getToolByName(obj, 'portal_workflow').getInfoFor(obj, 'review_state')
    else:
        state = None

    if WATERMARK and state in ['published', 'featured']:
        img = ImageExtender(obj).fields[0].get(obj)
    else:
        img = obj.getImage()

    fd, filename = tempfile.mkstemp('_' + obj.getId())
    os.close(fd)
    fout = open(filename, 'wb')
    fout.write(img.data)
    fout.close()

    info = IPTCInfo(filename, force=True)
    info.data['object name'] = obj.Title()
    info.data['caption/abstract'] = obj.Description()
    info.data['by-line'] = obj.Creator()
    info.data['copyright notice'] = obj.Rights()
    info.data['keywords'] = [i for i in obj.Subject()]
    info.keyword = info.data['keywords']
    info.data['sub-location'] = obj.getLocation().strip()
    info.data['city'] = obj.getLocation().strip()
    info.data['province/state'] = obj.getLocation().strip()
    info.data['country/primary location name'] = obj.getLocation().strip()
    info.data['country/primary location code'] = obj.getLocation().strip()
    info.save()

    if WATERMARK:
        # Set the original image field to have the updated IPTC
        fin = open(filename)
        ImageExtender(obj).fields[0].set(obj, fin.read())
        fin.close()

        if state in ['published', 'featured']:
            applyWatermark(obj)
        else:
            obj.setImage(ImageExtender(obj).fields[0].get(obj))
    else:
        fin = open(filename)
        obj.setImage(fin.read())
        fin.close()
