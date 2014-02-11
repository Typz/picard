# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006,2011 Lukáš Lalinský
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import os
from PyQt4 import QtCore, QtGui, QtNetwork
from picard import config, log
from picard.album import Album
from picard.track import Track
from picard.file import File
from picard.metadata import is_front_image
from picard.util import webbrowser2, encode_filename


class ActiveLabel(QtGui.QLabel):

    """Clickable QLabel."""

    clicked = QtCore.pyqtSignal()
    imageDropped = QtCore.pyqtSignal(QtCore.QUrl)

    def __init__(self, active=True, *args):
        QtGui.QLabel.__init__(self, *args)
        self.setMargin(0)
        self.setActive(active)
        self.setAcceptDrops(False)

    def setActive(self, active):
        self.active = active
        if self.active:
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        else:
            self.setCursor(QtGui.QCursor())

    def mouseReleaseEvent(self, event):
        if self.active and event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if url.scheme() in ('http', 'file'):
                event.acceptProposedAction()
                break

    def dropEvent(self, event):
        accepted = False
        for url in event.mimeData().urls():
            if url.scheme() in ('http', 'file'):
                accepted = True
                self.imageDropped.emit(url)
        if accepted:
            event.acceptProposedAction()


class CoverArtBox(QtGui.QGroupBox):

    def __init__(self, parent):
        QtGui.QGroupBox.__init__(self, "")
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(0)
        # Kills off any borders
        self.setStyleSheet('''QGroupBox{background-color:none;border:1px;}''')
        self.setFlat(True)
        self.release = None
        self.data = None
        self.item = None
        self.metadata = None
        self.currentImage = 0
        self.shadow = QtGui.QPixmap(":/images/CoverArtShadow.png")
        self.coverArt = ActiveLabel(False, parent)
        self.coverArt.setPixmap(self.shadow)
        self.coverArt.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.coverArt.clicked.connect(self.open_release_page)
        self.coverArt.imageDropped.connect(self.fetch_remote_image)
        self.layout.addWidget(self.coverArt, 0)
        self.coverArtLabel = QtGui.QLabel(parent)
        self.layout.addWidget(self.coverArtLabel, 0)
        self.layout.addStretch()
        self.selectorlayout = QtGui.QHBoxLayout()
        self.prevCoverArt = QtGui.QToolButton(parent)
        self.prevCoverArt.setText("<")
        self.prevCoverArt.clicked.connect(lambda : self.__select_image(self.currentImage - 1))
        self.prevCoverArt.hide()
        self.covertArtCount = QtGui.QLabel()
        self.covertArtCount.setText("")
        self.covertArtCount.setAlignment(QtCore.Qt.AlignHCenter)
        self.covertArtCount.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        self.nextCoverArt = QtGui.QToolButton()
        self.nextCoverArt.setText(">")
        self.nextCoverArt.clicked.connect(lambda : self.__select_image(self.currentImage + 1))
        self.nextCoverArt.hide()
        self.selectorlayout.addWidget(self.prevCoverArt)
        self.selectorlayout.addWidget(self.covertArtCount)
        self.selectorlayout.addWidget(self.nextCoverArt)
        self.removeCoverArt = QtGui.QToolButton(parent)
        self.removeCoverArt.setText("x")
        self.removeCoverArt.setToolTip(_(u"Remove artwork"))
        self.removeCoverArt.clicked.connect(self.remove_image)
        self.removeCoverArt.hide()
        self.selectorlayout.addWidget(self.removeCoverArt, 0)
        self.layout.addItem(self.selectorlayout)
        self.setLayout(self.layout)

    def show(self):
        self.__set_data(self.data, True)
        QtGui.QGroupBox.show(self)

    def __set_data(self, data, force=False, pixmap=None):
        if not force and self.data == data:
            return

        self.data = data
        if not force and self.isHidden():
            return

        cover = self.shadow
        label = ""
        if self.data:
            if pixmap is None:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(self.data["data"])
            if not pixmap.isNull():
                label = str(pixmap.width()) + " x " + str(pixmap.height())
                offx, offy, w, h = (1, 1, 121, 121)
                cover = QtGui.QPixmap(self.shadow)
                pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                painter = QtGui.QPainter(cover)
                bgcolor = QtGui.QColor.fromRgb(0, 0, 0, 128)
                painter.fillRect(QtCore.QRectF(offx, offy, w, h), bgcolor)
                x = offx + (w - pixmap.width()) / 2
                y = offy + (h - pixmap.height()) / 2
                painter.drawPixmap(x, y, pixmap)
                painter.end()
        self.coverArt.setPixmap(cover)
        self.coverArtLabel.setText(label)

    def set_metadata(self, metadata, item):
        self.item = item
        self.metadata = metadata
        self.currentImage = 0
        data = None
        if metadata and metadata.images:
            for image in metadata.images:
                if is_front_image(image):
                    data = image
                    break
                self.currentImage += 1
            else:
                # There's no front image, choose the first one available
                data = metadata.images[0]
        self.__set_data(data)
        self.__update_image_count()
        if item and metadata:
            self.coverArt.setAcceptDrops(True)
        else:
            self.coverArt.setAcceptDrops(False)
        release = None
        if metadata:
            release = metadata.get("musicbrainz_albumid", None)
        if release:
            self.coverArt.setActive(True)
            self.coverArt.setToolTip(_(u"View release on MusicBrainz"))
        else:
            self.coverArt.setActive(False)
            self.coverArt.setToolTip("")
        self.release = release

    def __update_image_count(self):
        count = 0
        if self.metadata and self.metadata.images:
            count = len(self.metadata.images)
        self.removeCoverArt.setVisible(count > 0)
        self.covertArtCount.setText(str(self.currentImage + 1) + "/" + str(count))
        self.covertArtCount.setVisible(count > 1)
        self.prevCoverArt.setVisible(count > 1)
        self.nextCoverArt.setVisible(count > 1)

    def __select_image(self, index):
        metadata = self.metadata
        if metadata and metadata.images and index >= 0 and index < len(metadata.images):
            self.currentImage = index
            self.__set_data(metadata.images[index])
            self.__update_image_count()

    def open_release_page(self):
        host = config.setting["server_host"]
        port = config.setting["server_port"]
        url = "http://%s:%s/release/%s" % (host, port, self.release)
        webbrowser2.open(url)

    def fetch_remote_image(self, url):
        if self.item is None:
            return
        if url.scheme() == 'http':
            path = url.encodedPath()
            if url.hasQuery():
                path += '?' + url.encodedQuery()
            self.tagger.xmlws.get(url.encodedHost(), url.port(80), path,
                self.on_remote_image_fetched, xml=False,
                priority=True, important=True)
        elif url.scheme() == 'file':
            path = encode_filename(unicode(url.toLocalFile()))
            if os.path.exists(path):
                f = open(path, 'rb')
                mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
                data = f.read()
                f.close()
                self.load_remote_image(mime, data)

    def on_remote_image_fetched(self, data, reply, error):
        mime = str(reply.header(QtNetwork.QNetworkRequest.ContentTypeHeader).toString())
        if mime in ('image/jpeg', 'image/png'):
            return self.load_remote_image(mime, data)
        if reply.url().hasQueryItem("imgurl"):
            #This may be a google images result, try to get the URL which is encoded in the query
            url = QtCore.QUrl(reply.url().queryItemValue("imgurl"))
            self.fetch_remote_image(url)
        else:
            log.warning("Can't load image with MIME-Type %s", mime)

    def remove_image(self):
        if isinstance(self.item, Album):
            album = self.item
            album.metadata.remove_image(self.currentImage)
            for track in album.tracks:
                track.metadata.remove_image(self.currentImage)
            for file in album.iterfiles():
                file.metadata.remove_image(self.currentImage)
        elif isinstance(self.item, Track):
            track = self.item
            track.metadata.remove_image(self.currentImage)
            for file in track.iterfiles():
                file.metadata.remove_image(self.currentImage)
        elif isinstance(self.item, File):
            file = self.item
            file.metadata.remove_image(self.currentImage)
        if self.currentImage < len(self.metadata.images):
            self.__select_image(self.currentImage)
        elif self.metadata.images:
            self.__select_image(self.currentImage - 1)
        else:
            self.__set_data(None)
            self.__update_image_count()

    def load_remote_image(self, mime, data):
        pixmap = QtGui.QPixmap()
        if not pixmap.loadFromData(data):
            log.warning("Can't load image")
            return
        self.__set_data([mime, data], pixmap=pixmap)
        if isinstance(self.item, Album):
            album = self.item
            album.metadata.add_image(mime, data)
            for track in album.tracks:
                track.metadata.add_image(mime, data)
            for file in album.iterfiles():
                file.metadata.add_image(mime, data)
        elif isinstance(self.item, Track):
            track = self.item
            track.metadata.add_image(mime, data)
            for file in track.iterfiles():
                file.metadata.add_image(mime, data)
        elif isinstance(self.item, File):
            file = self.item
            file.metadata.add_image(mime, data)
        self.currentImage = len(self.metadata.images) - 1
        self.__update_image_count()
