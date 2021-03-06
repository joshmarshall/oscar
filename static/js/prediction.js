var init = function() {
    $('.nominee-entry').not('.locked').click(function(e) {
        var el = $(this);
        var parent = el.parent();
        if (parent.hasClass("locked"))
            return;
        var category_id = parent.attr('id');
        parent.find("."+category_id).each(function() {
            $(this).removeClass("selected");
        });
        el.addClass("selected");
        $("#"+category_id+"-value").val(el.attr("id"));
    });
    
    $('.locked').each(function() {
        $(this).css("opacity", 0.7);
    });
    
    
}


$(init);
