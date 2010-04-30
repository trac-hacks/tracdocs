<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav">
 <h2>Docs Navigation</h2>
 <ul>
  <?cs if: len(docs.history) > 0 ?><li><?cs
  each:h = docs.history ?><?cs
    set:last = name(h) == len(docs.history) - #1 ?>
    <a href="<?cs var:h.href ?>"><?cs var:h.name ?></a><?cs
    if:!last ?> : <?cs
    /if ?><?cs
  /each ?></li>
  <?cs /if ?>
  <li class="last"><a href="<?cs var:docs.log_href ?>">
   Revision Log</a></li>
 </ul>
 <hr />
</div>

<?cs if:docs.debug ?>
<div class="debug">
<?cs var:docs.debug ?>
</div>
<?cs /if ?>

<div id="content" class="wiki">

<?cs var:docs.index ?>

<?cs if:len(docs.entries) > 0 ?>
<p/>
<div class="indent">
<?cs each:entry = docs.entries ?>
<div class="<?cs var:entry.kind ?>">
<a href="<?cs var:entry.href ?>"><?cs var:entry.name ?></a><?cs 
  if:entry.ext ?><div class="ext">(<?cs 
  var:entry.ext ?>)</div><?cs 
/if ?>
</div>
<?cs /each ?>
</div>
<?cs /if ?>

<?cs if docs.action == "view" ?>
<div id="wikipage">
  <?cs if:docs.content ?>
  <?cs var:docs.content ?>
  <?cs /if ?>
</div>
<?cs /if ?>

<?cs if docs.editable &&
  (docs.action == "edit" || docs.action == "preview" || docs.action == "collision") ?>
<h1>Editing "<?cs var:docs.page_name ?>"</h1>
<?cs if docs.action == "preview" ?>
<table id="info" >
  <tbody><tr><th>
  Preview of future version <?cs var:$docs.version+1 ?> (modified by <?cs var:docs.author ?>)
  </th></tr><tr>
  <td class="message"><?cs var:docs.comment ?></td></tr></tbody>
</table> 
<fieldset id="preview">
  <legend>Preview (<a href="#edit">skip</a>)</legend>
  <div id="wikipage"><?cs var:docs.content ?></div>
</fieldset><?cs
  elif docs.action =="collision"?>
<div class="system-message">
  Sorry, this page has been modified by somebody else since you started
  editing. Your changes cannot be saved.
</div>
<?cs /if ?>

<form id="edit" action="<?cs var:docs.current_href ?>" method="post">

<input type="hidden" name="action" value="edit" />
<input type="hidden" name="version" value="<?cs var:docs.version ?>" />

<textarea id="text" name="text" cols="80" rows="30" 
  style="font-family: monospace; font-size: 1.0em;"><?cs 
  var:docs.page_source ?></textarea>

<p />

<fieldset id="changeinfo">
  <legend>Change information</legend>
  <?cs if:trac.authname == "anonymous" ?>
  <div class="field">
    <label>Your email or username:<br />
    <input id="author" type="text" name="author" size="30" value="<?cs
      var:docs.author ?>" /></label>
  </div>
  <?cs /if ?>

  <div class="field">
    <label>Comment about this change (optional):<br />
    <input id="comment" type="text" name="comment" size="60" value="<?cs 
      var:docs.comment?>" />
    </label>
  </div>
</fieldset>

<br />

<div class="buttons">
 <?cs if docs.action == "collision" ?>
  <input type="submit" name="preview" value="Preview" disabled="disabled" />&nbsp;
  <input type="submit" name="save" value="Submit changes" disabled="disabled" />&nbsp;
 <?cs else ?>
  <input type="submit" name="preview" value="Preview" accesskey="r" />&nbsp;
  <input type="submit" name="save" value="Submit changes" />&nbsp;
 <?cs /if ?>
  <input type="submit" name="cancel" value="Cancel" />
</div>

</form>

<?cs /if ?>


<?cs if docs.editable && docs.action == "view" && 
  (trac.acl.WIKI_MODIFY || trac.acl.WIKI_DELETE) ?>

<div class="buttons">
<?cs if:trac.acl.WIKI_MODIFY ?>
<form method="get" action="<?cs var:docs.current_href ?>"><div>
  <input type="hidden" name="action" value="edit" />
  <input type="submit" value="Edit this page" accesskey="e" />
</form>
<?cs /if ?>
</div>

<?cs /if ?>

<?cs include "footer.cs"?>

