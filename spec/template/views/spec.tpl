%setdefault('toc', None)
%setdefault('is_doc', False)
% rebase('base.tpl', stylesheet='spec.css')
% import re
% tmpRef = '../' if is_doc else ''
% page = doc_attributes.get('name', '')
% is_index = page == 'Index'
% has_toc = bool(toc) and len(toc) > 1
% # Doorstop's format_level() drops a trailing ".0" only when the level is
% # longer than three characters, so "1.1.0" becomes "1.1" but a top-level
% # "1.0" survives and a section ends up looking like a sibling of its own
% # requirements. Numbering is presentation, and this is the presentation.
% section_number = lambda text: re.sub(r'^(\d+)\.0(\s)', r'\1\2', text)
% body = re.sub(r'(<h1\b[^>]*>)(\d+)\.0(\s)', r'\1\2\3', body)
% # The sidebar is narrow and every entry already links to the item, so the
% # UID Doorstop appends to each label is repetition the reader pays for.
% toc_label = lambda text: re.sub(r'\s*\([A-Z][A-Z0-9-]*\)$', '', section_number(text))
% # Doorstop names the index and the matrix after itself. Nobody is here to
% # read Doorstop; they are here to read a coffee machine specification.
% renamed = {'Index': 'Coffee machine specification',
%            'Traceability': 'Traceability matrix'}
% page_title = renamed.get(page) or doc_attributes.get('title', '')
% meta = [('Ref', doc_attributes.get('ref', '-')),
%         ('By', doc_attributes.get('by', '-')),
%         ('Issue', '{}{}'.format(doc_attributes.get('major', '-'),
%                                 doc_attributes.get('minor', '')))]
<header class="masthead">
  <div class="masthead-row">
    <div class="masthead-identity">
      % if is_doc:
      <span class="doc-name">{{page}}</span>
      % end
      <span class="doc-title">{{!page_title}}</span>
    </div>
    <dl class="doc-meta">
      % for label, value in meta:
      % if value and value != '-':
      <div><dt>{{label}}</dt><dd>{{value}}</dd></div>
      % end
      % end
    </dl>
  </div>
  <nav class="masthead-nav">
    <a href="{{baseurl}}{{tmpRef}}index.html">Overview</a>
    <a href="{{baseurl}}{{tmpRef}}documents/REQ-BREW.html">Specification</a>
    <a href="{{baseurl}}{{tmpRef}}traceability.html">Traceability</a>
    <a href="{{baseurl}}{{tmpRef}}test-coverage.html">Test coverage</a>
    <a href="{{baseurl}}{{tmpRef}}risk-analysis.html">Risk analysis</a>
  </nav>
</header>
<div class="layout{{'' if has_toc else ' no-toc'}}">
  % if has_toc:
  <aside class="toc">
    <div class="toc-title">Contents</div>
    <ul>
      % old_depth = 1
      % for entry in toc:
      % if entry['depth'] > 0:
      % for _ in range(entry['depth'] - old_depth):
      <li class="toc-branch"><ul>
      % end
      % for _ in range(old_depth - entry['depth']):
      </ul></li>
      % end
      <li><a href="#{{entry['uid']}}">{{toc_label(entry['text'])}}</a></li>
      % old_depth = entry['depth']
      % end
      % end
      % for _ in range(old_depth - 1):
      </ul></li>
      % end
    </ul>
  </aside>
  % end
  % if is_index:
  <main class="spec-body is-page landing">
    <p class="lede">Four artefacts, all written by the same pipeline run from
    the files in <code>spec/</code>, <code>src/</code> and <code>tests/</code>.
    None of them is maintained by hand.</p>
    <ul class="cards">
      <li>
        <a href="{{baseurl}}documents/REQ-BREW.html">Specification</a>
        <span>Seven requirements in three sections, compiled from Markdown.</span>
      </li>
      <li>
        <a href="{{baseurl}}traceability.html">Traceability matrix</a>
        <span>Every requirement in the document, as Doorstop links them.</span>
      </li>
      <li>
        <a href="{{baseurl}}test-coverage.html">Test coverage</a>
        <span>Which test proves which requirement, and whether it passed.</span>
      </li>
      <li>
        <a href="{{baseurl}}risk-analysis.html">Risk analysis</a>
        <span>What the specification does not say yet.</span>
      </li>
    </ul>
  </main>
  % else:
  % bodyClass = 'spec-body is-document' if is_doc else 'spec-body is-page'
  <main class="{{bodyClass}}">
    {{!body}}
  </main>
  % end
</div>
