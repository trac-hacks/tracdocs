
# stdlib imports
import re

# trac imports
from trac.core import *
from trac.mimeview.api import Mimeview, IContentConverter, Context
from trac.perm import IPermissionRequestor
from trac.search import ISearchSource, shorten_result
from trac.util import get_reporter_id
from trac.util.html import html, Markup
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_ctxtnav, add_stylesheet, add_script, add_link
from trac.versioncontrol.api import Node
from trac.versioncontrol.svn_fs import SubversionRepository



class TracDocsPlugin(Component):
    implements(IContentConverter, INavigationContributor, IPermissionRequestor,
               IRequestHandler, ITemplateProvider, ISearchSource)

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('WIKI_VIEW'):
            yield ('docs', 'Docs', 1)

    def get_search_results(self, req, query, filters):
        if 'docs' not in filters:
            return

        if not req.perm.has_permission('WIKI_VIEW'):
            return

        root = self.config.get('docs', 'root', '')
        repos = self.env.get_repository(authname=req.authname)
        node = repos.get_node(root, None)

        if not isinstance(query, list):
            results = []
            for term in re.split('(".*?")|(\'.*?\')|(\s+)', query):
                if term != None and term.strip() != '':
                    if term[0] == term[-1] == "'" or term[0] == term[-1] == '"':
                        term = term[1:-1]
                    results.append(term)
            query = results
        query = [q.lower() for q in query]

        patterns = []
        for q in query:
            q = re.sub('\s+', '\s+', q)
            p = re.compile(q, re.IGNORECASE | re.MULTILINE)
            patterns.append(p)

        to_unicode = Mimeview(self.env).to_unicode

        def walk(node):
            if node.path.endswith('.txt') or node.path.endswith('.rst'):
                yield node
            if node.kind == Node.DIRECTORY:
                for subnode in node.get_entries():
                    for result in walk(subnode):
                        yield result

        for node in walk(node):
            matched = 1
            content_length = node.get_content_length()
            if content_length > (1024 * 1024):
                continue
            content = node.get_content()
            if not content:
                continue
            content = to_unicode(content.read(), node.get_content_type())
            for p in patterns:
                if p.search(content) is None:
                    matched = 0
                    break
            if matched:
                change = repos.get_changeset(node.rev)
                path = node.path[len(root)+1:]
                yield (self.env.href.docs(path),
                       path, change.date, change.author,
                       shorten_result(content.replace('\n', ' '), query))

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('txt', 'Plain Text', 'txt', 'text/x-rst', 'text/plain', 9)

    def convert_content(self, req, mimetype, content, key):
        # Tell the browser that the content should be downloaded and
        # not rendered. The x=y part is needed to keep Safari from being 
        # confused by the multiple content-disposition headers.
        req.send_header('Content-Disposition', 'attachment; x=y')

        return (content, 'text/plain;charset=utf-8')

    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['WIKI_VIEW']
        return actions + [('WIKI_ADMIN', actions)]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'docs'
    def get_navigation_items(self, req):
        if not req.perm.has_permission('WIKI_VIEW'):
            return
        yield ('mainnav', 'docs',
            html.A('Docs', href= req.href.docs()))

    # IRequestHandler methods
    def match_request(self, req):
        import re
        match = re.match(r'/docs(?:(/.*))?', req.path_info)
        if match:
            path, = match.groups()
            req.args['path'] = path or '/'
            return True

    def process_request(self, req):
        req.perm.require('WIKI_VIEW')

        action = req.args.get('action', 'view')
        version = req.args.get('version')
        root = self.config.get('docs', 'root', '')
        base = req.args.get('path')
        if base[-1] == '/':
            base = base[:-1]
        path = root + base

        title = base or 'Docs'
        if action != 'view':
            title += ' (%s)' % action
        data = {}
        data['title'] = title

        repos = self.env.get_repository(authname=req.authname)
        node = repos.get_node(path, None)

        if node.isdir:
            page = DirPage(self.env, node, root, base)
        else:
            page = FilePage(self.env, node, root, base)

        data['editable'] = not node.isdir

        if req.method == 'POST':

            if action == 'edit':
                if page.node.isdir:
                    raise TracError("Cannot edit a directory")
                latest_version = page.version
                if req.args.has_key('cancel'):
                    req.redirect(req.href.docs(page.base))
                elif int(version) != latest_version:
                    action = 'collision'
                    self._render_editor(req, page, data)
                elif req.args.has_key('preview'):
                    action = 'preview'
                    self._render_editor(req, page, data, preview=True)
                else:
                    self._do_save(req, page)

        elif action == 'edit':
            self._render_editor(req, page, data)

        else:
            req.perm.assert_permission('WIKI_VIEW')

            if node.isdir:
                data['entries'] = page.get_entries(req)
                if page.index is not None:
                    data['index'] = page.index.get_html(req)
                else:
                    mimeview = Mimeview(self.env)
                    text = []
                    text.append('=' * (len(page.name) + 6))
                    text.append('   %s' % page.name)
                    text.append('=' * (len(page.name) + 6))
                    text = '\n'.join(text)
                    mimetype = 'text/x-rst; charset=utf8'
                    result = mimeview.render(Context.from_request(req), mimetype, text)
                    data['index'] = result

            else:
                mime_type, chunk = page.get_raw()

                # When possible, send with non-text mimetype
                # Perhaps we should embed images...? 
                if not mime_type.startswith('text') or \
                    mime_type.startswith('text/html'):
                    req.send_response(200)
                    req.send_header('Content-Type', mime_type)
                    req.send_header('Content-Length', len(chunk))
                    req.end_headers()
                    req.write(chunk)
                    return

                format = req.args.get('format')
                if format:
                    Mimeview(self.env).send_converted(req, 'text/x-rst', chunk, format, page.name)

                for conversion in Mimeview(self.env).get_supported_conversions('text/x-rst'):
                    conversion_href = req.href.docs(page.base, format=conversion[0])
                    add_link(req, 'alternate', conversion_href, conversion[1],
                             conversion[3])

                # Render the content into HTML
                data['content'] = page.get_html(req)


        data['action'] = action
        data['current_href'] = req.href.docs(page.base)
        data['log_href'] = req.href.log(page.path)

        # Include trac wiki stylesheet
        add_stylesheet(req, 'common/css/wiki.css')

        # Include trac docs stylesheet
        add_stylesheet(req, 'docs/common.css')

        # Include docutils stylesheet
        add_stylesheet(req, 'docs/docutils.css')

        # Include google-code-prettify
        add_stylesheet(req, 'docs/prettify.css')
        add_script(req, 'docs/prettify.min.js')

        # Include context navigation links
        history = [('root', req.href.docs())]
        t = ''
        for s in base[1:].split('/'):
            if not s: continue
            t += '/' + s
            history.append((s, req.href.docs(t)))
        for h in reversed(history):
            add_ctxtnav(req, h[0], h[1])
        add_ctxtnav(req, 'Revision Log', req.href.log(path))

        return 'docs.html', data, None

    def _do_save(self, req, page):
        if not page.exists:
            req.perm.assert_permission('WIKI_CREATE')
        else:
            req.perm.assert_permission('WIKI_MODIFY')

        text = req.args.get('text', '').encode('utf-8')
        text = text.replace('\r\n', '\n')
        comment = req.args.get('comment', '').encode('utf-8')

        page.save(req, text, comment)
        req.redirect(req.href.docs(page.base))

    def _render_editor(self, req, page, data, preview=False):
        req.perm.assert_permission('WIKI_MODIFY')

        if page.node.isdir:
            raise TracError("Cannot edit a directory.")

        if req.args.has_key('text'):
            page.mime_type = 'text/x-rst; charset=utf8'
            page.chunk = req.args.get('text')
        else:
            page.get_raw()

        author = get_reporter_id(req, 'author')
        comment = req.args.get('comment', '')

        # FIXME: self._set_title(req, page, 'edit')

        if preview:
            data['content'] = page.get_html(req)

        data['page_name'] = page.base
        data['page_source'] = page.chunk
        data['version'] = page.version
        data['author'] = author
        data['comment'] = comment


    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('docs', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]




class Page(object):

    def __init__(self, env, node, root, base):
        self.env = env
        self.node = node
        self.root = root
        self.base = base
        self.path = path = root + base
        self.version = self.node.rev

        slash = base.rfind('/')
        dot = base.rfind('.')
        left = max(slash+1, 0)
        right = max(dot, len(base))
        self.name = base[left:right]
        self.dir = base[:slash]



class DirPage(Page):

    def __init__(self, env, node, root, base):
        super(DirPage, self).__init__(env, node, root, base)

        try:
            path = self.path
            indexfile = path.endswith('/') and 'index.txt' or '/index.txt'
            indexnode = node.repos.get_node(path + indexfile)
            self.index = FilePage(env, indexnode, root, base + indexfile)
        except TracError:
            self.index = None

    def get_entries(self, req):
        entries = []
        def sortkey(x):
            dot = x.name.rfind('.')
            if dot > 0:
                return (x.kind, x.name[:dot], x.name)
            else:
                return (x.kind, x.name, x.name)

        if self.name:
            entries.append({
                    'name': '..',
                    'ext' : '',
                    'kind': 'dir',
                    'href': req.href.docs(self.dir),
                    })

        for e in sorted(self.node.get_entries(), key=sortkey):

            # Skip the index file
            if e.name == 'index.txt': continue

            # Detect file extensions
            dot = e.name.rfind('.')
            if dot > 0:
                name = e.name[:dot]
                ext  = e.name[dot+1:]
            else:
                name = e.name
                ext  = ''
            entries.append({
                'name': name.replace('-', ' '),
                'ext' : ext,
                'kind': e.kind,
                'href': req.href.docs(self.base + '/' + e.name),
                })
        return entries



class FilePage(Page):

    def __init__(self, env, node, root, base):
        super(FilePage, self).__init__(env, node, root, base)
        self.mimeview = Mimeview(self.env)
        self.exists = (node is not None)

        self.mime_type = None
        self.chunk = None

    def get_html(self, req):
        """
        Get the raw content from the repository and convert to html.
        """
        mime_type, chunk = self.get_raw()
        if not mime_type.startswith('text'):
            raise TracError("Invalid mime-type: %s" % mime_type)

        # Hack to support images, we change the path from relative
        # the document being requested to absolute.
        # 1: Ignore http and ftp urls to allow images to be fetched
        # 2: Assume URLS beginning with "/" are relative to top-level
        # 3: Assume URLS that do not include "http/ftp" are relative to
        #    current path.
        def fixup(m):
            text = m.group(1)
            if text.startswith('http:') or text.startswith('ftp:'):
                return m.group(0)
            if text.startswith('/'):
                text = text[1:]
            dir = self.dir
            if dir.endswith('/'):
                dir = dir[:-1] 
            return '.. image:: %s/%s' % (req.href.docs(dir), text)
        chunk = re.sub('\.\. image\:\:\s*(\S+)', fixup, chunk, re.MULTILINE)

        # Assume all wiki pages are ReStructuredText documents 
        result = self.mimeview.render(Context.from_request(req), mime_type, chunk)

        if not isinstance(result, (str, unicode)):
            result = unicode(result)

        # Hack to pretty-print source code (assumes all literal-blocks 
        # contain source code).
        result = result.replace('<pre class="literal-block">',
                                '<pre class="literal-block prettyprint">')

        if 'prettyprint' in result:
            # FIXME: Add as an event listener instead?
            result += """
                <script type="text/javascript">
                var origOnLoad = window.onload;
                function onLoad() {
                    if (origOnLoad) {
                      if(typeof(origOnLoad) == "string") {
                        eval(origOnLoad);
                      }
                      else {
                        origOnLoad();
                      }
                    } 
                    prettyPrint();
                }
                window.onload = onLoad;
                </script>
            """

        return Markup(result)

    def get_raw(self):
        """
        Load the raw content from the repository.
        """
        if self.mime_type is not None:
            return self.mime_type, self.chunk

        node = self.node
        content_length = node.get_content_length()
        if content_length > (1024 * 1024):
            raise TracError("Docs is too large: %d" % content_length)
        content = node.get_content()
        chunk = content.read(content_length)
        mime_type = node.content_type

        # Guess the mime-type when possible to be text/plain.
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = self.mimeview.get_mimetype(node.name, chunk) or \
            mime_type or 'text/plain'

        if mime_type.startswith('text/plain'):
            mime_type = 'text/x-rst; charset=utf8' 

        self.mime_type = mime_type
        self.chunk = chunk

        return mime_type, chunk 

    def save(self, req, text, comment):
        """
        Save the specified text into this document.
        """
        if not isinstance(self.node.repos, SubversionRepository):
            raise TracError("The '%s' repository is not supported" % type(self.node.repos))

        from svn import core as _core
        from svn import fs as _fs
        from svn import repos as _repos

        repos = self.node.repos.repos #.repos
        revnum = self.node.rev
        author = req.authname
        message = 'Edited %s' % self.base[1:]
        if comment:
            message += ' (%s)' % comment

        pool = _core.Pool()
        fs_txn = _repos.fs_begin_txn_for_commit(repos, revnum, author, message, pool)
        fs_root = _fs.svn_fs_txn_root(fs_txn, pool)
        if hasattr(self.node, '_scoped_svn_path'):
            fs_path = self.node._scoped_svn_path
        else:
            fs_path = self.node._scoped_path_utf8
        stream = _fs.svn_fs_apply_text(fs_root, fs_path, None, pool)
        _core.svn_stream_write(stream, text)
        _core.svn_stream_close(stream) 
        return _repos.fs_commit_txn(repos, fs_txn, pool)



