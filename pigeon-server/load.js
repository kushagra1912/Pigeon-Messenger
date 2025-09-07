import http from "k6/http";
import {check, sleep} from "k6"


export function hit() { 
    let uuid1 = "fdee2e57-9dca-47f3-94d5-9dbbbf46a7e2"
    let uuid2 = "8356329c-0960-4ae2-9f28-7b0aacdf48b4"
    let datetime = "2019-10-12T07:20:50.52Z"
    let url = "http://server-998006746.us-east-1.elb.amazonaws.com/api/v1/" + "messages/" ; 

    const payload = JSON.stringify({
        "meta": {
            "to": uuid2,
            "from": uuid1,
            "datetime": datetime,
            },
        
        "message": "This is a test!"
    }); 
  
    const params = { 
       headers: { 
          'Accept': 'application/json', 
       }, 
    }; 
  
    let response = http.post(url + uuid1, payload, params); 
    check(response, { 
       'is status 201': (r) => r.status === 201, 
    }); 

  
    sleep(1); 
  
    response = http.get(url + uuid2); 
    check(response, { 
       'is status 200': (r) => r.status === 200,
    }); 
    
    sleep(2); 
}


export const options = { 
    scenarios: { 
       hits: { 
          exec: 'hit', 
          executor: "ramping-vus", 
          stages: [ 
             { duration: "4m", target: 10000 }
          ], 
       }
    }, 
 };