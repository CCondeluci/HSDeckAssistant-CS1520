var _validFileExtensions = [".jpg", ".jpeg", ".gif", ".png", ".webp"];
function validateFile()
{
    var pic = document.getElementById("in_pic");
    if (pic.type == "file")
    {
        var filename = pic.value;
        if(filename.length > 0)
        {
            var valid = false;
            for (var i=0; i< _validFileExtensions.length; i++)
            {
                var curExt = _validFileExtensions[i];
                if(filename.substr(filename.length - curExt.length, curExt.length).toLowerCase() == curExt)
                {
                    valid = true;
                }
            }
            if(!valid)
            {
                alert(filename + " contains an invalid extension. Allowed extensions are: " + _validFileExtensions.join(", "));
                return false;
            }
        }
        
    }
    return true;
}