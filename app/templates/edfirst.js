$(document.body).on('click', '#btnChange', function(e){
        $("#para1").css('font-family', 'Karla Tamil Upright');
      })
      $(document.body).on('change', '#chooseParaFont', function(e){
        var whichFont = "'" + $(this).val() + "'"
        $("#contentFont").remove();
        newSheet = '<link href="' 
                + 'http://fonts.googleapis.com/css?family='
                + whichFont
                + ':400,700" rel="stylesheet" type="text/css" id="contentFont">';
        $('head').append(newSheet)
        $(".para1").css('font-family', whichFont);
      })
      $(document.body).on('change', '#chooseMenuFont', function(e){
        var whichFont = "'" + $(this).val() + "'"
        $("#navFont").remove();
        newSheet = '<link href="' 
                + 'http://fonts.googleapis.com/css?family='
                + whichFont
                + ':400,700" rel="stylesheet" type="text/css" id="navFont">';
        $('head').append(newSheet)
        $(".nav").css('font-family', whichFont);
      })

      $(document.body).on('change', '#chooseHeaderFont', function(e){
        var whichFont = "'" + $(this).val() + "'"
        $("#headerFont").remove();
        newSheet = '<link href="' 
                + 'http://fonts.googleapis.com/css?family='
                + whichFont
                + ':400,700" rel="stylesheet" type="text/css" id="navFont">';
        $('head').append(newSheet)
        $(".hdr").css('font-family', whichFont);
      })

      $(document.body).on('change', '#chooseFontSize', function(e){
        $(".para1").css('font-size', $("#chooseFontSize").val())
      })

      $(document.body).on('change', '#chooseMenuFontSize', function(e){
        $(".nav").css('font-size', $("#chooseMenuFontSize").val())
      })

      $(document.body).on('change', '#chooseHeaderFontSize', function(e){
        $(".hdr").css('font-size', $("#chooseHeaderFontSize").val())
      })

      $(document.body).on('click', '.lnk', function(e){
        alert('This type of link would go to the online Questionnaires Page hopefully in the appropriate language')
      })
