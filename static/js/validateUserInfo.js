var usernameValidated = false;
var returnResult = -1;
var ui_timeOut;
var _validFileExtensions = [".jpg", ".jpeg", ".gif", ".png", ".webp"];
$(document).ready(function(){
    $('#usernameField').keyup(function(){
        clearTimeout(ui_timeOut);
        ui_timeOut = setTimeout(function(){checkAvailability();},600);
    });
    $('#submitButton').click(function(){
        if(usernameValidated)
        {
            if(validateFile())
                return true;
            else
                return false;
        }
        else{
            if(returnResult==0){
                alert('Your username has already been taken.');
            }
            else{alert('Your username is improperly formatted or contains illegal characters. Please fix it and try again.');}
            return false;
        }
    });

});
function checkAvailability()
{
    var username = $('#usernameField').val();
    $.post('/check_availability', {username: username},
        function(result){
            if(result==1)
            {
                $('#usernametakendiv').html('<img src=/static/assets/check.png></img>');
            }
            else if(result==0)
            {
                $('#usernametakendiv').html('<img src=/static/assets/redx.png></img>');
            }
            else if(result==-1)
            {
                $('#usernametakendiv').html('Usernames must be 3-12 characters long and can contain only alphanumeric characters and underscores (_)');
            }
            returnResult=result;
            result==1?usernameValidated=true:usernameValidated=false;
        });
}
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

